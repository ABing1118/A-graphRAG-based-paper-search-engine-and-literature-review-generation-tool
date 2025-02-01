import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import CloseIcon from '@mui/icons-material/Close';  // 需要安装 @mui/icons-material

const SubNetwork = ({ data, loading, onClose }) => {
    const subSvgRef = useRef(null);
    
    useEffect(() => {
        if (!data) return;
        
        const svg = d3.select(subSvgRef.current);
        svg.selectAll("*").remove();
        
        if (loading) {
            // 显示加载动画
            const width = 850;
            const height = 600;
            
            svg.append("text")
                .attr("x", width / 2)
                .attr("y", height / 2)
                .attr("text-anchor", "middle")
                .attr("dominant-baseline", "middle")
                .text("Loading citation network...")
                .attr("fill", "#666")
                .attr("font-size", "20px");
                
            return;
        }
        
        const width = 850;
        const height = 600;
        
        // 创建一个容器来包含所有元素
        const container = svg.append("g");

        // 创建缩放行为
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on("zoom", (event) => {
                container.attr("transform", event.transform);
            });

        // 应用缩放
        svg.call(zoom)
           .call(
               zoom.transform,
               d3.zoomIdentity
                 .translate(width / 2, height / 2)
                 .scale(0.8)
                 .translate(-width / 2, -height / 2)
           );

        // 添加引用量的比例尺
        const citationScale = d3.scaleLinear()
            .domain([
                d3.min(data.nodes, d => d.citations_count || 0),
                d3.max(data.nodes, d => d.citations_count || 0)
            ])
            .range([5, 15]);  // 节点范围稍微小一点

        // 添加箭头标记定义
        container.append("defs").append("marker")
            .attr("id", "subarrowhead")  // 使用不同的ID避免冲突
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", 10)  // 和主图保持一致
            .attr("refY", 0)
            .attr("markerWidth", 8)
            .attr("markerHeight", 8)
            .attr("orient", "auto")
            .append("path")
            .attr("d", "M0,-5L10,0L0,5")
            .attr("fill", "#999");

        // 创建力导向图
        const simulation = d3.forceSimulation(data.nodes)
            .force("link", d3.forceLink(data.edges)
                .id(d => d.id)
                .distance(100)
                .strength(0.4)
            )
            .force("charge", d3.forceManyBody()
                .strength(-200)
                .distanceMax(300)
            )
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide()
                .radius(d => {
                    const citations = d.citations_count || 0;
                    const nodeRadius = citations === 0 ? 5 : citationScale(citations);
                    return nodeRadius + 10;
                })
                .strength(1)
            )
            .alphaDecay(0.1);

        // 绘制连线
        const links = container.append("g")
            .selectAll("path")
            .data(data.edges)
            .enter()
            .append("path")
            .attr("stroke", "#999")
            .attr("stroke-opacity", 0.6)
            .attr("stroke-width", 1)
            .attr("fill", "none")
            .attr("marker-end", "url(#subarrowhead)");

        // 绘制节点
        const nodes = container.append("g")
            .selectAll("circle")
            .data(data.nodes)
            .enter()
            .append("circle")
            .attr("r", d => {
                if (d.type === "center") return 10;
                const citations = d.citations_count || 0;
                return citations === 0 ? 5 : citationScale(citations);
            })
            .attr("fill", d => {
                switch(d.type) {
                    case "center": return "#ff4444";
                    case "citation": return "#4444ff";
                    case "reference": return "#44ff44";
                    default: return "#999";
                }
            })
            .style("cursor", "pointer");

        // 添加节点标签
        const labels = container.append("g")
            .selectAll("text")
            .data(data.nodes)
            .enter()
            .append("text")
            .text(d => d.title)
            .attr("font-size", "10px")
            .attr("dx", d => {
                const r = d.type === "center" ? 12 : 8;
                return r;
            })
            .attr("dy", 3)
            .attr("fill", "#333")
            .style("pointer-events", "none");

        // 添加tooltip
        const tooltip = d3.select("body").append("div")
            .attr("class", "subnetwork-tooltip")
            .style("position", "absolute")
            .style("visibility", "hidden")
            .style("background", "white")
            .style("padding", "5px")
            .style("border", "1px solid #ddd")
            .style("border-radius", "4px")
            .style("pointer-events", "none")
            .style("z-index", 1100);

        // 添加节点交互
        nodes
            .on("mouseover", (event, d) => {
                tooltip.style("visibility", "visible")
                    .html(`
                        <strong>${d.title}</strong><br/>
                        类型: ${d.type === "center" ? "中心论文" : 
                               d.type === "citation" ? "引用本文" : "被本文引用"}<br/>
                        ${d.type !== "center" ? `引用量: ${d.citations_count || 0}<br/>
                        年份: ${d.year || '未知'}` : ''}
                    `);
            })
            .on("mousemove", (event) => {
                tooltip
                    .style("top", (event.pageY - 10) + "px")
                    .style("left", (event.pageX + 10) + "px");
            })
            .on("mouseout", () => {
                tooltip.style("visibility", "hidden");
            });

        // 更新力导向图位置
        simulation.on("tick", () => {
            links.attr("d", d => {
                const sourceRadius = d.source.citations_count ? 
                    citationScale(d.source.citations_count) : 5;
                const targetRadius = d.target.citations_count ? 
                    citationScale(d.target.citations_count) : 5;
                
                // 计算方向向量
                const dx = d.target.x - d.source.x;
                const dy = d.target.y - d.source.y;
                const dr = Math.sqrt(dx * dx + dy * dy);
                
                // 计算起点和终点（考虑节点半径）
                if (dr === 0) return "M0,0L0,0";
                
                const sourceX = d.source.x + (dx * sourceRadius) / dr;
                const sourceY = d.source.y + (dy * sourceRadius) / dr;
                const targetX = d.target.x - (dx * targetRadius) / dr;
                const targetY = d.target.y - (dy * targetRadius) / dr;
                
                return `M${sourceX},${sourceY}L${targetX},${targetY}`;
            });

            nodes
                .attr("cx", d => d.x)
                .attr("cy", d => d.y);

            labels
                .attr("x", d => d.x)
                .attr("y", d => d.y);
        });

        return () => {
            // 清理tooltip
            tooltip.remove();
        };
    }, [data, loading]);
    
    return (
        <div className="modal-overlay" 
             style={{
                 position: 'fixed',
                 top: 0,
                 left: 0,
                 right: 0,
                 bottom: 0,
                 backgroundColor: 'rgba(0, 0, 0, 0.5)',  // 半透明黑色背景
                 display: 'flex',
                 justifyContent: 'center',
                 alignItems: 'center',
                 zIndex: 1000
             }}>
            <div className="modal-content"
                 style={{
                     position: 'relative',
                     background: 'white',
                     padding: '20px',
                     borderRadius: '8px',
                     boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
                     width: '900px',  // 固定宽度
                     height: '650px'   // 固定高度
                 }}>
                <button
                    onClick={onClose}
                    style={{
                        position: 'absolute',
                        right: '10px',
                        top: '10px',
                        background: 'none',
                        border: 'none',
                        cursor: 'pointer',
                        padding: '5px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                    }}>
                    <CloseIcon />
                </button>
                <h3 style={{ marginTop: 0, marginBottom: '15px' }}>
                    {loading ? "Loading Citation Network..." : "Citation Network"}
                </h3>
                <svg ref={subSvgRef} width="850" height="600"></svg>
            </div>
        </div>
    );
};

export default SubNetwork; 