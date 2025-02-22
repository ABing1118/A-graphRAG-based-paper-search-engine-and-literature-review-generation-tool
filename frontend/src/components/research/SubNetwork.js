import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import CloseIcon from '@mui/icons-material/Close';  // 需要安装 @mui/icons-material

const SubNetwork = ({ data, loading, onClose, fullPage = false }) => {
    const subSvgRef = useRef(null);
    
    useEffect(() => {
        // 确保数据完整且不在加载状态
        if (!data || !data.nodes || !data.edges || loading) return;
        
        const svg = d3.select(subSvgRef.current);
        svg.selectAll("*").remove();
        
        const width = svg.node().getBoundingClientRect().width;
        const height = svg.node().getBoundingClientRect().height;
        
        // 使用实际尺寸而不是固定值
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
                 .scale(1.2)
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

        // 添加与主网络一致的颜色比例尺
        const colorScale = d3.scaleSequential()
            .domain([
                d3.min(data.nodes, d => d.year), 
                d3.max(data.nodes, d => d.year)
            ])
            .interpolator(d3.interpolate("#1565C0", "#90CAF9"));

        // 计算中间年份对应的颜色
        const minYear = d3.min(data.nodes, d => d.year);
        const maxYear = d3.max(data.nodes, d => d.year);
        const middleYear = Math.floor((minYear + maxYear) / 2);
        const centerColor = colorScale(middleYear);

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
                const citations = d.citations_count || 0;
                const baseRadius = citations === 0 ? 5 : citationScale(citations);
                // 中心节点稍微大一点，但不会过大
                return d.type === "center" ? Math.max(baseRadius, 8) : baseRadius;
            })
            .style('fill', d => d.type === "center" ? centerColor : colorScale(d.year))
            .style('stroke', d => d.type === 'center' ? '#ff4444' : 'none')
            .style('stroke-width', d => d.type === 'center' ? 3 : 0)
            .style("cursor", "pointer");

        // 添加节点标签
        const labels = container.append("g")
            .selectAll("text")
            .data(data.nodes)
            .enter()
            .append("text")
            .text(d => d.title)
            .attr("font-size", d => d.type === "center" ? "12px" : "10px")
            .attr("font-weight", d => d.type === "center" ? "bold" : "normal")
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
                let typeDescription;
                switch(d.type) {
                    case "center":
                        typeDescription = "Center paper";
                        break;
                    case "citation":
                        typeDescription = "Cited by this paper";
                        break;
                    case "reference":
                        typeDescription = "Cited by this paper";
                        break;
                    case "citation_to_citation":
                        typeDescription = "Cited by the paper that cited this paper";
                        break;
                    case "citation_to_reference":
                        typeDescription = "Cited by the paper that cited this paper";
                        break;
                    case "reference_to_citation":
                        typeDescription = "Cited by the paper that was cited by this paper";
                        break;
                    case "reference_to_reference":
                        typeDescription = "Cited by the paper that was cited by this paper";
                        break;
                    default:
                        typeDescription = "Unknown type";
                }
                
                tooltip.style("visibility", "visible")
                    .html(`
                        <strong>${d.title}</strong><br/>
                        Type: ${typeDescription}${d.type !== "center" ? `<br/>
                        Citations: ${d.citations_count || 0}<br/>
                        Year: ${d.year || 'Unknown'}` : ''}
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
    
    // 只在数据准备就绪时才渲染 SVG
    if (!data || !data.nodes || !data.edges || loading) {
        return null;  // 返回 null 而不是渲染空的 SVG
    }
    
    return (
        <svg 
            ref={subSvgRef} 
            width="100%" 
            height="100%"
            style={{ 
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)'
            }}
        />
    );
};

export default SubNetwork; 