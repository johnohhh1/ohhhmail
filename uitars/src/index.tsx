/**
 * UI-TARS Application Entry Point
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import { log } from './config';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

log.info('UI-TARS initializing...');

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
