import React, { forwardRef } from 'react';
import {
  List,
  ListItem,
  Card,
  CardContent,
  Typography,
  Box,
} from '@mui/material';

const PaperList = forwardRef(({ 
    papers, 
    selectedPaperId,
    hoveredPaperId,
    onPaperSelect,
    onPaperHover
}, ref) => {
  // 处理空数据情况
  if (!papers.length) {
    return <p>没有找到结果</p>;
  }

  return (
    <List ref={ref} sx={{ p: 2 }}>
      {papers.map((paper) => (
        <ListItem key={paper.id} sx={{ px: 0, py: 1 }}>
          <Card 
            data-paper-id={paper.id}  // 添加data属性用于滚动定位
            onClick={() => onPaperSelect(paper)}
            onMouseEnter={() => onPaperHover(paper.id)}
            onMouseLeave={() => onPaperHover(null)}
            sx={{
              width: '100%',
              // 背景色：选中时为淡蓝色(8%透明度)，未选中时为40%透明度的白色
              background: paper.id === selectedPaperId 
                ? 'rgba(25, 118, 210, 0.08)'
                : 'rgba(255, 255, 255, 0.2)',  // 降低单个卡片的透明度
              backdropFilter: 'blur(2px)',      // 减小模糊效果让背景粒子更清晰
              cursor: 'pointer',                // 鼠标样式：手型
              '&:hover': {                      // 悬停效果
                background: 'rgba(25, 118, 210, 0.08)',  // 悬停时背景色
                transform: 'translateY(-2px)',           // 上移2px
                transition: 'all 0.3s ease-in-out'       // 0.3秒过渡动画
              }
            }}
          >
            <CardContent>
              {/* 论文标题 */}
              <Typography 
                variant="subtitle1" 
                component="div" 
                gutterBottom
                sx={{ 
                  // 字体粗细：选中时加粗
                  fontWeight: paper.id === selectedPaperId ? 'bold' : 'medium',
                  lineHeight: 1.2,  // 行高：1.2倍
                  mb: 1            // 下边距：1个单位（8px）
                }}
              >
                {paper.title}
              </Typography>
              {/* 作者信息 */}
              <Typography 
                variant="body2" 
                color="text.secondary"
                sx={{ fontSize: '0.875rem' }}  // 字体大小：14px
              >
                作者: {paper.authors.join(', ')}
              </Typography>
              {/* 年份和引用信息 */}
              <Box sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: 2,                    // 元素间距：2个单位（16px）
                mt: 1,                     // 上边距：1个单位（8px）
                fontSize: '0.75rem',        // 字体大小：12px
                color: 'text.secondary'     // 次要文本颜色
              }}>
                <span>{paper.year}</span>
                <span>引用: {paper.citations}</span>
              </Box>
            </CardContent>
          </Card>
        </ListItem>
      ))}
    </List>
  );
});

PaperList.displayName = 'PaperList';

export default PaperList; 