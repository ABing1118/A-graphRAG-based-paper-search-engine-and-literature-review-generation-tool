import React, { useCallback } from 'react';
import Particles from "react-tsparticles";
import { loadSlim } from "tsparticles-slim";

const ParticleBackground = () => {
  // 初始化粒子系统的回调函数
  const particlesInit = useCallback(async engine => {
    await loadSlim(engine);
  }, []);

  return (
    <Particles
      id="tsparticles"
      init={particlesInit}
      options={{
        background: {
          color: {
            value: "#f0f7ff",  // 背景颜色：浅蓝色。可以使用任何颜色代码，如 #ffffff 为白色
          },
        },
        particles: {
          color: {
            value: "#1976d2",  // 粒子颜色：深蓝色。可以使用任何颜色代码
          },
          links: {
            color: "#1976d2",    // 连接线颜色：与粒子相同
            distance: 150,       // 粒子之间可连接的最大距离（像素）
            enable: true,        // 启用粒子之间的连接线
            opacity: 0.2,        // 连接线透明度：0.2 = 20%透明度
            width: 1,           // 连接线宽度（像素）
          },
          move: {
            enable: true,        // 启用粒子运动
            speed: 1,           // 粒子运动速度：1 = 慢速，增大数值会加快速度
            direction: "none",   // 运动方向：none=随机，可选 "top"/"bottom"/"left"/"right"
            random: false,       // 随机运动
            straight: false,     // 直线运动
            outModes: {
              default: "bounce", // 触碰边界时的行为：bounce=弹回，out=消失后从对面出现
            },
            attract: {
              enable: true,      // 启用粒子间吸引力
              rotateX: 2000,     // X轴吸引力：数值越大吸引力越小
              rotateY: 2000,     // Y轴吸引力：数值越大吸引力越小
            },
          },
          number: {
            density: {
              enable: true,      // 启用密度控制
              area: 1000,        // 密度计算区域：数值越大，粒子越稀疏
            },
            value: 120,          // 粒子总数：增减该值可改变粒子数量
          },
          opacity: {
            value: 0.2,         // 粒子透明度：0.2 = 20%透明度
          },
          size: {
            value: { min: 1, max: 5 },  // 粒子大小范围：最小1像素，最大5像素
          },
        },
        interactivity: {
          events: {
            onHover: {
              enable: true,      // 启用鼠标悬停交互
              mode: "grab",      // 悬停模式：grab=抓取效果
            },
          },
          modes: {
            grab: {
              distance: 200,     // 鼠标影响半径（像素）
              links: {
                opacity: 0.5,    // 鼠标悬停时连接线透明度
              },
            },
          },
        },
        detectRetina: true,      // 启用视网膜显示支持，保证高分辨率显示
      }}
      style={{
        position: 'absolute',    // 绝对定位，铺满整个容器
        top: 0,                 // 顶部对齐
        left: 0,               // 左侧对齐
        width: '100%',         // 宽度100%
        height: '100%',        // 高度100%
        zIndex: 0,            // 层级：0表示在最底层
      }}
    />
  );
};

export default ParticleBackground; 