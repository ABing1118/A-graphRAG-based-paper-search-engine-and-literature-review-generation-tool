import React from 'react';
import {
  Box,
  Typography,
  Chip,
  Paper,
  Divider,
  Link
} from '@mui/material';
import { CalendarToday, School, Bookmark } from '@mui/icons-material';

const PaperDetail = ({ paper }) => {
  // 当没有选中论文时显示的默认状态
  if (!paper) {
    return (
      <Paper
        sx={{
          height: '100%',                        // 占满容器高度
          display: 'flex',                       // 弹性布局
          alignItems: 'center',                  // 垂直居中
          justifyContent: 'center',              // 水平居中
          background: 'rgba(255, 255, 255, 0.05)', // 更透明的白色背景
          backdropFilter: 'blur(2px)',           // 背景模糊效果
          p: 3,                                  // 内边距
        }}
      >
        <Typography 
          color="text.secondary"
          sx={{ 
            textAlign: 'center',                 // 文字居中
            fontSize: '1.1rem',                  // 字体大小
            fontWeight: 'medium'                 // 字体粗细
          }}
        >
          请选择一篇论文查看详细信息
        </Typography>
      </Paper>
    );
  }

  // 显示选中论文的详细信息
  return (
    <Paper
      sx={{
        p: 3,                                    // 内边距
        height: '100%',                          // 占满容器高度
        overflow: 'auto',                        // 内容溢出时显示滚动条
        background: 'rgba(255, 255, 255, 0.1)',  // 半透明白色背景
        backdropFilter: 'blur(5px)',             // 背景模糊效果
        transition: 'all 0.3s ease-in-out'       // 平滑过渡效果
      }}
    >
      {/* 论文标题 */}
      <Typography variant="h5" gutterBottom sx={{ fontWeight: 'bold' }}>
        {paper.title}
      </Typography>

      {/* 论文基本信息：年份、期刊、引用次数 */}
      <Box sx={{ mb: 2, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        {/* 年份信息 */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <CalendarToday fontSize="small" color="primary" />
          <Typography variant="body2">
            {paper.publication_date || paper.year}
          </Typography>
        </Box>
        {/* 期刊信息 */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <School fontSize="small" color="primary" />
          <Typography variant="body2">{paper.journal}</Typography>
        </Box>
        {/* 引用次数 */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Bookmark fontSize="small" color="primary" />
          <Typography variant="body2">引用: {paper.citations}</Typography>
        </Box>
      </Box>

      <Divider sx={{ my: 2 }} /> {/* 分隔线 */}

      {/* 作者信息 */}
      <Typography variant="h6" gutterBottom>作者</Typography>
      <Typography variant="body2" sx={{ mb: 2 }}>
        {paper.authors.join(', ')}
      </Typography>

      {/* 研究领域 */}
      {paper.fields && paper.fields.length > 0 && (
        <>
          <Typography variant="h6" gutterBottom>研究领域</Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
            {paper.fields.map((field, index) => (
              <Chip 
                key={index}
                label={field}
                size="small"
                color="primary"
                variant="outlined"
              />
            ))}
          </Box>
        </>
      )}

      {/* 摘要信息 */}
      <Typography variant="h6" gutterBottom>摘要</Typography>
      <Typography variant="body2" sx={{ mb: 2 }}>
        {paper.abstract}
      </Typography>

      {/* 链接 */}
      {(paper.url || paper.pdf_url) && (
        <>
          <Typography variant="h6" gutterBottom>链接</Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            {paper.url && (
              <Link href={paper.url} target="_blank" rel="noopener">
                论文页面
              </Link>
            )}
            {paper.pdf_url && (
              <Link href={paper.pdf_url} target="_blank" rel="noopener">
                PDF下载
              </Link>
            )}
          </Box>
        </>
      )}
    </Paper>
  );
};

export default PaperDetail; 