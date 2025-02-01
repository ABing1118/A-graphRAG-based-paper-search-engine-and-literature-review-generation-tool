import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { fetchCitationNetwork } from '../../api/papers';
import './CitationNetwork.css';

const CitationNetwork = ({ 
    query, 
    topK, 
    onNodeClick,  // 新增：处理节点点击
    onNodeHover,  // 新增：处理节点悬停
    selectedPaperId,  // 新增：当前选中的论文ID
    hoveredPaperId   // 新增：当前悬停的论文ID
}) => {
    const svgRef = useRef(null);
    const nodesRef = useRef(null);  // 添加一个ref来存储nodes选择器

    // 移动到组件级别的更新函数
    const updateNodesState = () => {
        if (nodesRef.current) {
            nodesRef.current
                .attr("stroke", d => {
                    if (d.id === selectedPaperId) return "#ff4444";
                    if (d.id === hoveredPaperId) return "#4444ff";
                    return "#fff";
                })
                .attr("stroke-width", d => {
                    if (d.id === selectedPaperId) return 3;
                    if (d.id === hoveredPaperId) return 2;
                    return 1;
                });
        }
    };

    // 监听属性变化的useEffect移到组件级别
    useEffect(() => {
        updateNodesState();
    }, [selectedPaperId, hoveredPaperId]);

    const renderNetwork = (data) => {
        const svg = d3.select(svgRef.current);
        
        // 清除现有内容
        svg.selectAll("*").remove();

        // 获取容器尺寸
        const width = svg.node().getBoundingClientRect().width;
        const height = svg.node().getBoundingClientRect().height;

        // 创建一个容器来包含所有元素
        const container = svg.append("g");

        // 创建缩放行为
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])  // 缩放范围
            .on("zoom", (event) => {
                container.attr("transform", event.transform);
            });

        // 应用缩放，并设置初始位置和缩放
        svg.call(zoom)
           .call(
               zoom.transform,
               d3.zoomIdentity
                 .translate(width / 2, height / 2) 
                 .scale(0.5)  
                 .translate(-width / 2, -height / 2)
           );

        // 创建力导向图(仅在这部分做布局的改动)
        const simulation = d3.forceSimulation(data.nodes)
            // 1. 连接力 - 控制有连线节点之间的距离
            .force("link", d3.forceLink(data.edges)
                .id(d => d.id)
                .distance(200)  
                .strength(0.4)
            )
            // 2. 电荷力 - 排斥/吸引
            .force("charge", d3.forceManyBody()
                .strength(-300)   // 负值表示排斥,可调大以让节点更分散
                .distanceMax(500) // 排斥力作用范围上限
            )
            // 3. 中心力 - 将所有节点往中心拉
            .force("center", d3.forceCenter(width / 2, height / 2))
            // 4. 碰撞力 - 防止节点重叠
            .force("collision", d3.forceCollide()
                .radius(d => {
                    const baseSize = 4;
                    const citations = d.citations_count || 0;
                    const nodeRadius = citations === 0 
                        ? baseSize 
                        : Math.min(baseSize + Math.sqrt(citations) * 1.2, 20);
                    return nodeRadius + 15;  // 这里增加额外间距
                })
                .strength(10)  // 这个值越大，碰撞效果越强
            )
            // 5. alphaDecay - 减缓衰减,让布局多迭代一会更稳定
            .alphaDecay(0.1);

        // 定义颜色比例尺 (保持你的逻辑)
        const colorScale = d3.scaleSequential()
            .domain([
                d3.min(data.nodes, d => d.year), 
                d3.max(data.nodes, d => d.year)
            ])
            // 使用自定义的蓝色范围，确保最浅的颜色也足够可见
            // .interpolator(d3.interpolate("#4A90E2", "#E3F2FD"))  // 从深蓝到浅蓝
            // 或者使用这个更深的范围
            .interpolator(d3.interpolate("#1565C0", "#90CAF9"))  // 从更深的蓝到中等的蓝

        // 绘制连线
        const links = container.append("g")
            .selectAll("line")
            .data(data.edges)
            .enter()
            .append("line")
            .attr("stroke", "#2a5a8c")
            .attr("stroke-opacity", 0.4) // 降低透明度,减少密集线的干扰
            .attr("stroke-width", 2);

        // 绘制节点
        const nodes = container.append("g")
            .selectAll("circle")
            .data(data.nodes)
            .enter()
            .append("circle")
            .attr("r", d => {
                const baseSize = 5;
                const citations = d.citations_count || 0;
                return citations === 0
                    ? baseSize
                    : Math.min(baseSize + Math.sqrt(citations), 30);
            })
            .attr("fill", d => colorScale(d.year))
            .attr("stroke", d => d.id === selectedPaperId ? "#ff4444" : "#fff")  // 选中状态边框
            .attr("stroke-width", d => d.id === selectedPaperId ? 3 : 1)         // 选中状态边框宽度
            .style("cursor", "pointer");  // 添加鼠标手型

        // 保存nodes引用
        nodesRef.current = nodes;

        // 初始更新节点状态
        updateNodesState();

        // 添加节点标签
        const labels = container.append("g")
            .selectAll("text")
            .data(data.nodes)
            .enter()
            .append("text")
            .text(d => d.title.substring(0, 25) + "...")
            .attr("font-size", "10px")
            .attr("dx", 12)
            .attr("dy", 3)
            .attr("fill", "#333")
            .style("pointer-events", "none");

        // 修改节点的事件处理
        nodes
            .on("click", (event, d) => {
                // 添加调试日志
                console.log('Clicked node:', d);
                if (onNodeClick) {
                    onNodeClick(d);
                }
            })
            .on("mouseover", function(event, d) {
                // 保持原有的 tooltip 功能
                const tooltip = d3.select(".tooltip");
                tooltip.style("visibility", "visible")
                    .html(`
                        <strong>${d.title}</strong><br/>
                        Year: ${d.year}<br/>
                        Citations: ${d.citations_count}
                    `);
                
                // 调用父组件传入的悬停回调
                if (onNodeHover) {
                    onNodeHover(d);
                }
            })
            .on("mousemove", function(event) {
                // 保持原有的 tooltip 移动功能
                d3.select(".tooltip")
                    .style("top", (event.pageY - 120) + "px")
                    .style("left", (event.pageX - 500) + "px");
            })
            .on("mouseout", function() {
                // 隐藏 tooltip
                d3.select(".tooltip").style("visibility", "hidden");
                
                // 清除悬停状态
                if (onNodeHover) {
                    onNodeHover(null);
                }
            });

        // 更新力导向图位置
        simulation.on("tick", () => {
            links
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            nodes
                .attr("cx", d => d.x)
                .attr("cy", d => d.y);

            labels
                .attr("x", d => d.x)
                .attr("y", d => d.y);
        });
    };

    useEffect(() => {
        const fetchAndRenderNetwork = async () => {
            try {
                const data = await fetchCitationNetwork(query, topK);
                if (data) {
                    renderNetwork(data);
                }
            } catch (error) {
                console.error('Failed to fetch citation network:', error);
            }
        };

        fetchAndRenderNetwork();
    }, [query, topK]);

    return (
        <div className="citation-network">
            <svg ref={svgRef} width="100%" height="100%"></svg>
            <div className="tooltip"></div>
        </div>
    );
};

export default CitationNetwork;
