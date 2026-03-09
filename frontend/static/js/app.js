import { InitializeAuth, RefreshCurrentUser, UpdateAuthUI } from './auth.js';
import { InitializeTabs, loadPanel } from './tabs.js';
import './manage.js'; import './users.js';
import './query.js';

window.APP_STATE = {
    //baseUrl : localStorage.getItem('backend') || 'http://localhost:5000'
    baseUrl : 'http://localhost:5000'
};

InitializeAuth();
RefreshCurrentUser().then(UpdateAuthUI);
InitializeTabs();
loadPanel('query');