import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import theme from './theme';
import SearchPage from './pages/SearchPage';
import SearchResults from './pages/SearchResults';
import SubNetworkPage from './pages/SubNetworkPage';

const App = () => {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Routes>
          <Route path="/" element={<SearchPage />} />
          <Route path="/results" element={<SearchResults />} />
          <Route path="/subnetwork" element={<SubNetworkPage />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
};

export default App;
