import { loadPanel } from './tabs.js';

// 初始化
export function InitializeAuth()
{
    // 浮窗打开、关闭事件
    document.getElementById('btn-open-login').addEventListener('click', () => OpenModal('login'));
    document.getElementById('btn-open-register').addEventListener('click', () => OpenModal('register'));
    document.getElementById('btn-open-modify-password').addEventListener('click', () => OpenModal('modifyPassword'));
    document.getElementById('modal-close').addEventListener('click', CloseModal);
    // 浮窗切换事件
    document.getElementById('btn-switch-register').addEventListener('click', () => SwitchModal('register'));
    document.getElementById('btn-switch-login').addEventListener('click', () => SwitchModal('login'));
    // 登录、注册事件
    document.getElementById('btn-do-login').addEventListener('click', TryLogin);
    document.getElementById('btn-do-register').addEventListener('click', TryRegister);
    // 登出、修改密码事件
    document.getElementById('btn-logout').addEventListener('click', Logout);
    document.getElementById('btn-modify-password').addEventListener('click', TryModifyPassword);
}

function Esc(s)
{
    if(s === null || s === undefined)
        return '';
    return String(s).replace(/[&<>"']/g, m => ({
        '&':'&amp;',
        '<':'&lt;',
        '>':'&gt;',
        '"':'&quot;',
        "'":'&#039;'
    }[m]));
}

function OpenModal(mode='login')
{
    const modalBackdrop = document.getElementById('modal-backdrop');
    modalBackdrop.classList.remove('hidden');
    modalBackdrop.classList.add('flex');
    if(mode === 'modifyPassword') {
        document.getElementById('modify-password-status').innerHTML = '';
        document.getElementById('login-form').style.display = 'none';
        document.getElementById('register-form').style.display = 'none';
        document.getElementById('modify-password-form').style.display = 'block';
        document.getElementById('modal-title').innerHTML = '修改密码';
    }
    else if(mode === 'login' || mode === 'register')
        SwitchModal(mode)
    else
        CloseModal();
}

function SwitchModal(to_mode='login')
{
    document.getElementById('login-status').innerHTML = '';
    document.getElementById('reg-status').innerHTML = '';
    document.getElementById('login-form').style.display = (to_mode==='login') ? 'block' : 'none';
    document.getElementById('register-form').style.display = (to_mode==='register') ? 'block' : 'none';
    document.getElementById('modal-title').innerHTML = (to_mode==='login') ? '登录' : '注册';
}

function CloseModal()
{
    document.getElementById('reg-status').innerHTML = ''
    document.getElementById('login-status').innerHTML = ''
    document.getElementById('modify-password-status').innerHTML = '';
    document.getElementById('login-form').style.display = 'none';
    document.getElementById('register-form').style.display = 'none';
    document.getElementById('modify-password-form').style.display = 'none';
    const modalBackdrop = document.getElementById('modal-backdrop');
    modalBackdrop.classList.add('hidden');
    modalBackdrop.classList.remove('flex');
}

// try login
async function TryLogin()
{
    const statusEl = document.getElementById('login-status');
    const u = document.getElementById('login-username').value.trim();
    const p = document.getElementById('login-password').value;
    if(!u || !p) {
        statusEl.innerHTML = '请输入用户名和密码';
        return;
    }
    statusEl.innerHTML = '登录中...';
    try {
        const res = await fetch(
            `${window.APP_STATE.baseUrl}/auth/login`, {
                method: 'POST',
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify({username: u, password: p})
            }
        );
        const j = await res.json();
        if(res.ok && j.access_token) {
            localStorage.setItem('access_token', j.access_token);
            localStorage.setItem('refresh_token', j.refresh_token);
            localStorage.setItem('username', j.username);
            statusEl.innerHTML = '登录成功';
            await RefreshCurrentUser();
            UpdateAuthUI();
            CloseModal();
            statusEl.innerHTML = '';
        }
        else {
            statusEl.innerHTML = '登录失败，' + Esc(j.message || '');
        }
    }
    catch(e) {
        statusEl.innerHTML = '登录异常：' + e.message;
    }
}

// try register
async function TryRegister()
{
    const statusEl = document.getElementById('reg-status');
    const u = document.getElementById('reg-username').value.trim();
    const p = document.getElementById('reg-password').value;
    const p2 = document.getElementById('reg-password2').value;
    if(!u || !p) {
        statusEl.innerHTML = '请输入用户名和密码';
        return;
    }
    if(p.length < 8) {
        statusEl.innerHTML = '密码长度不能小于 8 位';
        return;
    }
    if(p !== p2) {
        statusEl.innerHTML = '两次输入密码不一致';
        return;
    }
    statusEl.innerHTML = '注册中...';
    try {
        const res = await fetch(
            `${window.APP_STATE.baseUrl}/auth/register`,
            {
                method:'POST',
                headers:{'Content-Type':'application/json'},
                body: JSON.stringify({username:u, password:p})
            }
        );
        const j = await res.json();
        if(res.ok) {
            statusEl.innerHTML = '注册成功，请登录';
        }
        else {
            statusEl.innerHTML = '注册失败，' + Esc(j.message || '');
        }
    }
    catch(e) {
        statusEl.innerHTML = '注册异常：' + e.message;
    }
}

// Logout
function Logout()
{
    window.APP_STATE.access_token = null;
    window.APP_STATE.refresh_token = null;
    window.APP_STATE.username = null;
    window.APP_STATE.isAnalyst = false;
    window.APP_STATE.isAdmin = false;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('username');
    UpdateAuthUI();
    loadPanel('query');
}

// try modify password
async function TryModifyPassword()
{
    const statusEl = document.getElementById('modify-password-status');
    const op = document.getElementById('old-password').value.trim();
    const np = document.getElementById('new-password').value;
    const np2 = document.getElementById('new-password2').value;
    if(!op || !np) {
        statusEl.innerHTML = '请输入旧密码和新密码';
        return;
    }
    if(np.length < 8) {
        statusEl.innerHTML = '新密码长度不能小于 8 位';
        return;
    }
    if(np !== np2) {
        statusEl.innerHTML = '两次输入密码不一致';
        return;
    }
    statusEl.innerHTML = '修改中...';
    try {
        const res = await fetchWithAuth(
            `${window.APP_STATE.baseUrl}/auth/modify_password`,
            {
                method: 'POST',
                headers: Object.assign(
                    {'Content-Type':'application/json'}
                ),
                body: JSON.stringify({old_password: op, new_password: np})
            }
        );
        const j = await res.json();
        if(res.ok) {
            statusEl.innerHTML = '修改密码成功，请重新登录';
            Logout();
        }
        else {
            statusEl.innerHTML = '修改密码失败，' + Esc(j.message || '');
        }
    }
    catch(e) {
        statusEl.innerHTML = '修改密码异常：' + e.message;
    }
}

// 使用 token 访问 url
export async function fetchWithAuth(url, options = {})
{
    options.headers = options.headers || {}
    options.headers['Authorization'] =
        window.APP_STATE.access_token ? 'Bearer ' + window.APP_STATE.access_token : '';
    let res = await fetch(url, options);
    if (res.status === 401 && window.APP_STATE.refresh_token) {
        const refreshRes = await fetch(
            `${window.APP_STATE.baseUrl}/auth/refresh`,
            {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${window.APP_STATE.refresh_token}` }
            }
        );
        if (refreshRes.ok) {
            const data = await refreshRes.json();
            localStorage.setItem('access_token', data.access_token);
            window.APP_STATE.access_token = data.access_token;
            console.log(window.APP_STATE.access_token);
            options.headers['Authorization'] = `Bearer ${window.APP_STATE.access_token}`;
            res = await fetch(url, options);
        }
        else {
            throw new Error('Refresh token 过期，请重新登录');
        }
    }
    return res;
}

export async function RefreshCurrentUser()
{
    window.APP_STATE.access_token = localStorage.getItem('access_token') || null;
    window.APP_STATE.refresh_token = localStorage.getItem('refresh_token') || null;
    window.APP_STATE.username = localStorage.getItem('username') || null;
    window.APP_STATE.isAnalyst = false;
    window.APP_STATE.isAdmin = false;
    try {
        const res = await fetchWithAuth(
            `${window.APP_STATE.baseUrl}/auth/me`,
            {headers:{}}
        );
        if (res.ok) {
            const j = await res.json();
            window.APP_STATE.username = j.username || window.APP_STATE.username;
            if(Array.isArray(j.roles) && j.roles.includes('analyst'))
                window.APP_STATE.isAnalyst = true;
            if(Array.isArray(j.roles) && j.roles.includes('admin'))
                window.APP_STATE.isAdmin = true;
        }
    }
    catch(e) {
        alert(e);
    }
}

export function UpdateAuthUI()
{
    if(window.APP_STATE.access_token) {
        document.getElementById('not-logged').style.display = 'none';
        document.getElementById('logged').style.display = 'inline-flex';
        document.getElementById('welcome-text').textContent=`欢迎，${window.APP_STATE.username}`;
    }
    else {
        document.getElementById('not-logged').style.display = 'inline-flex';
        document.getElementById('logged').style.display = 'none';
    }
    if(window.APP_STATE.isAnalyst)
        document.getElementById('tab-manage').classList.remove('hidden');
    else
        document.getElementById('tab-manage').classList.add('hidden');
    if(window.APP_STATE.isAdmin)
        document.getElementById('tab-users').classList.remove('hidden');
    else
        document.getElementById('tab-users').classList.add('hidden');
}