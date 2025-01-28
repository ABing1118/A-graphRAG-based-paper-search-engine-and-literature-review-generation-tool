import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { fetchCitationNetwork } from '../../api/papers';
import './CitationNetwork.css';

const CitationNetwork = ({ query, topK }) => {
    const svgRef = useRef(null);

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
                 .translate(width / 2, height / 2)  // 先移动到中心
                 .scale(0.5)  // 设置一个更合适的初始缩放值
                 .translate(-width / 2, -height / 2)  // 再移回原位
           );

        // 创建力导向图
        const simulation = d3.forceSimulation(data.nodes)
            .force("link", d3.forceLink(data.edges)
                .id(d => d.id)
                .distance(250))  // 增加连线长度，从150改为250
            .force("charge", d3.forceManyBody().strength(-100))  // 增加斥力，让节点分散得更开
            .force("center", d3.forceCenter(width / 2, height / 2))
            // 添加碰撞力，防止节点重叠
            .force("collision", d3.forceCollide().radius(d => Math.sqrt(d.citations_count || 1) * 2 + 5));  // 从 4 改为 2，间距从 10 改为 5

        // 定义颜色比例尺
        const colorScale = d3.scaleSequential()
            .domain([d3.min(data.nodes, d => d.year), d3.max(data.nodes, d => d.year)])
            .interpolator(d3.interpolateViridis);  // 使用更好看的颜色方案

        // 绘制连线
        const links = container.append("g")
            .selectAll("line")
            .data(data.edges)
            .enter()
            .append("line")
            .attr("stroke", "#2a5a8c")  // 保持蓝色
            .attr("stroke-opacity", 0.8)  // 增加不透明度，从0.6改为0.8
            .attr("stroke-width", 3);  // 增加线宽，从2改为3

        // 绘制节点
        const nodes = container.append("g")
            .selectAll("circle")
            .data(data.nodes)
            .enter()
            .append("circle")
            .attr("r", d => Math.sqrt(d.citations_count || 1) * 2)
            .attr("fill", d => colorScale(d.year))
            .attr("stroke", "#fff")
            .attr("stroke-width", 2)
            // .call(drag(simulation));

        // 添加节点标签
        const labels = container.append("g")
            .selectAll("text")
            .data(data.nodes)
            .enter()
            .append("text")
            .text(d => d.title.substring(0, 30) + "...")  // 显示更多文字
            .attr("font-size", "12px")  // 增大字号
            .attr("dx", 15)
            .attr("dy", 4)
            .attr("fill", "#333")
            .style("pointer-events", "none");

        // 修改节点的 hover 效果
        nodes.on("mouseover", function(event, d) {
            // 只处理 tooltip，不改变节点大小
            const tooltip = d3.select(".tooltip");
            tooltip.style("visibility", "visible")
                .html(`
                    <strong>${d.title}</strong><br/>
                    Year: ${d.year}<br/>
                    Citations: ${d.citations_count}
                `);
        }).on("mouseout", function() {
            d3.select(".tooltip").style("visibility", "hidden");
        });

        // 更新力导向图
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

    // 拖拽功能
    // const drag = (simulation) => {
    //     const dragstarted = (event) => {
    //         event.sourceEvent.stopPropagation();  // 阻止事件冒泡，防止触发缩放
    //         if (!event.active) simulation.alphaTarget(0.3).restart();
    //         event.subject.fx = event.subject.x;
    //         event.subject.fy = event.subject.y;
    //     };

    //     const dragged = (event) => {
    //         event.sourceEvent.stopPropagation();  // 阻止事件冒泡，防止触发缩放
    //         event.subject.fx = event.x;
    //         event.subject.fy = event.y;
    //     };

    //     const dragended = (event) => {
    //         event.sourceEvent.stopPropagation();  // 阻止事件冒泡，防止触发缩放
    //         if (!event.active) simulation.alphaTarget(0);
    //         event.subject.fx = null;
    //         event.subject.fy = null;
    //     };

    //     return d3.drag()
    //         .on("start", dragstarted)
    //         .on("drag", dragged)
    //         .on("end", dragended);
    // };

    return (
        <div className="citation-network">
            <svg ref={svgRef} width="100%" height="100%"></svg>
            <div className="tooltip"></div>
        </div>
    );
};

export default CitationNetwork; 