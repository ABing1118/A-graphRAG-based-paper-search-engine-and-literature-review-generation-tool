import React from 'react';
import {
  List,
  ListItem,
  Card,
  CardContent,
  Typography,
  Box,
} from '@mui/material';

const PaperList = ({ papers, selectedPaper, onSelectPaper }) => {
  // 处理空数据情况
  if (!papers.length) {
    return <p>没有找到结果</p>;
  }

  // 显示作者
  const renderAuthors = (authors) => {
    if (!authors || authors.length === 0) return "Unknown";
    // 如果 authors 是字符串数组，直接 join
    if (typeof authors[0] === 'string') return authors.join(', ');
    // 如果 authors 是对象数组，提取 name 属性
    if (typeof authors[0] === 'object') {
      return authors.map(author => author.name || 'Unknown').join(', ');
    }
    return "Unknown";
  };

  // 显示日期
  const formatDate = (date) => {
    if (!date) return "";
    return new Date(date).toLocaleDateString();
  };

  return (
    <List sx={{ 
      p: 2,                                    // 移除默认内边距
    }}>
      {papers.map((paper) => (
        <ListItem key={paper.id} sx={{ 
          px: 0,   // 水平内边距为0
          py: 1    // 垂直内边距为1个单位（8px）
        }}>
          <Card 
            sx={{ 
              width: '100%',     // 卡片宽度100%
              // 背景色：选中时为淡蓝色(8%透明度)，未选中时为40%透明度的白色
              background: paper.id === selectedPaper?.id 
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
            onClick={() => onSelectPaper(paper)}
          >
            <CardContent>
              {/* 论文标题 */}
              <Typography 
                variant="subtitle1" 
                component="div" 
                gutterBottom
                sx={{ 
                  // 字体粗细：选中时加粗
                  fontWeight: paper.id === selectedPaper?.id ? 'bold' : 'medium',
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
                作者: {renderAuthors(paper.authors)}
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
                <span>{formatDate(paper.year)}</span>
                <span>引用: {paper.citations}</span>
              </Box>
            </CardContent>
          </Card>
        </ListItem>
      ))}
    </List>
  );
};

export default PaperList; 