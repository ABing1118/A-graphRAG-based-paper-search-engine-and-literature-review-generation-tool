import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',  // 主色调：深蓝色
    },
    background: {
      default: '#f0f7ff',  // 默认背景色：浅蓝色
      paper: 'rgba(255, 255, 255, 0.8)',  // 卡片背景色：半透明白色
    },
  },
  components: {
    MuiAppBar: {
      styleOverrides: {
        root: {
          background: 'rgba(255, 255, 255, 0.8)',
          backdropFilter: 'blur(8px)',
        },
      },
    },
  },
});

export default theme; 