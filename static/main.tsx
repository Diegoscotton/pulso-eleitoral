import React from 'react';
import {createRoot} from 'react-dom/client';
import Home from '../app/page';
import '../app/globals.css';
(window as any).__STATIC_DASHBOARD__=true;
(window as any).__DASHBOARD_BASE__=import.meta.env.BASE_URL;
createRoot(document.getElementById('root')!).render(<Home/>);
