import { fetchWithAuth } from './auth.js';

export function Initialize() {
    // 查询按钮
    document.getElementById('btn-search-users').addEventListener('click', SearchUsers);
    // 管理按钮
    document.getElementById('btn-select-all').addEventListener('click',
        () => document.querySelectorAll('#users-results .user-checkbox').forEach(cb => cb.checked = true));
    document.getElementById('btn-select-none').addEventListener('click',
        () => document.querySelectorAll('#users-results .user-checkbox').forEach(cb => cb.checked = false));
    document.getElementById('btn-delete-selected').addEventListener('click', DeleteSelectedUsers);
    document.getElementById('btn-activate-selected').addEventListener('click', () => SetActivateSelectedUsers(true));
    document.getElementById('btn-freeze-selected').addEventListener('click', () => SetActivateSelectedUsers(false));
    document.getElementById('btn-resetpass-selected').addEventListener('click', ResetPasswordSelectedUsers);

    document.getElementById('btn-add-role').addEventListener('click', () => ModifyRoleForSelected('add'));
    document.getElementById('btn-remove-role').addEventListener('click', () => ModifyRoleForSelected('remove'));

    // 初始化用户列表
    SearchUsers();
}


/* ---------- 
- 工具函数
----------  */
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

// 渲染用户列表
function RenderUsers(users)
{
    const container = document.getElementById('users-results');
    container.innerHTML = '';
    if(!users || users.length === 0){
        container.innerHTML = `
            <div class="text-sm text-slate-500">无相关用户</div>
        `;
        return;
    }
    const table = document.createElement('table');
    table.className = 'table-auto w-full border-collapse border border-gray-300 bg-white';
    table.innerHTML = `
        <thead class="bg-gray-100">
            <tr>
                <th class="border border-gray-300 px-4 py-2 text-left">选择</th>
                <th class="border border-gray-300 px-4 py-2 text-left">用户名</th>
                <th class="border border-gray-300 px-4 py-2 text-left">ID</th>
                <th class="border border-gray-300 px-4 py-2 text-left">激活状态</th>
                <th class="border border-gray-300 px-4 py-2 text-left">角色</th>
            </tr>
        </thead>
        <tbody>
        </tbody>
    `;
    const tbody = table.querySelector('tbody');
    users.forEach(u => {
        const isAdmin = Array.isArray(u.roles) && u.roles.includes('admin');
        const row = document.createElement('tr');
        row.className = 'hover:bg-gray-50';
        row.setAttribute('data-user-id', Esc(u.user_id));
        row.setAttribute('data-roles', JSON.stringify(u.roles || []));
        row.setAttribute('data-is-admin', isAdmin ? '1' : '0');
        // 角色列表
        const rolesHtml = (u.roles && u.roles.length>0) ?
            u.roles.map(r =>`<span class="inline-block px-2 py-0.5 mr-2 mb-1 text-sm bg-slate-100 rounded">${Esc(r)}</span>`).join('') :
            '<span class="text-sm text-slate-400">无</span>';
        // 激活状态
        const activeStatus = u.is_active ?
            `<span class="text-md text-green-600 font-medium">激活</span>` :
            `<span class="text-md text-blue-600 font-medium">冻结</span>`;
        // 管理员标识
        const adminMark = isAdmin ?
            `<span class="ml-2 text-sm text-white bg-red-600 rounded px-2">Admin</span>` :
            '';
        row.innerHTML = `
            <td class="border border-gray-300 px-4 py-2">
                <input type="checkbox" class="user-checkbox" />
            </td>
            <td class="border border-gray-300 px-4 py-2">
                ${Esc(u.username)} ${adminMark}
            </td>
            <td class="border border-gray-300 px-4 py-2">
                ${Esc(u.user_id)}
            </td>
            <td class="border border-gray-300 px-4 py-2">
                ${activeStatus}
            </td>
            <td class="border border-gray-300 px-4 py-2">
                ${rolesHtml}
            </td>
        `;
        tbody.appendChild(row);
    });
    container.appendChild(table);
}

// 收集被勾选用户 id，并识别其中的 admin
function CollectSelectedUsers()
{
    const checks = Array.from(document.querySelectorAll('#users-results .user-checkbox:checked'));
    const all = checks.map(c => {
        const row = c.closest('[data-user-id]');
        const id = row?.getAttribute('data-user-id');
        const isAdmin = row?.getAttribute('data-is-admin') === '1';
        const roles = JSON.parse(row?.getAttribute('data-roles') || '[]');
        return { id, isAdmin, roles };
    }).filter(x => x.id);
    return all;
}

/* ---------- 
- 按钮事件函数
----------  */

// 按用户名搜索用户
async function SearchUsers(){
    document.getElementById('users-panel').classList.remove('hidden');
    document.getElementById('users-action-status').innerHTML = '';
    document.getElementById('role-action-status').innerHTML = '';
    const usernames = document.getElementById('username-search').value.trim();
    const container = document.getElementById('users-results');
    container.innerHTML = '查询中...';
    try {
        const res = await fetchWithAuth(
            `${window.APP_STATE.baseUrl}/users/query` + (usernames ? `?usernames=${encodeURIComponent(usernames)}` : ''), 
            {headers: {}}
        );
        const j = await res.json();
        if(!res.ok)
        {
            container.innerHTML = '查询失败，' + Esc(j.message || ''); 
            return;
        }
        const users = j.users || [];
        // expect users : [ {'user_id': 3, 'username': 'admin', roles:['admin', ...], is_active: True}, ...]
        RenderUsers(users);
    }
    catch(e) {
        container.innerHTML = '查询异常：' + e; 
    }
}

// 删除选中（跳过 admin）
async function DeleteSelectedUsers()
{
    const users = CollectSelectedUsers();
    const statusEl = document.getElementById('users-action-status');
    statusEl.innerHTML = '';
    if(users.length === 0) {
        statusEl.innerHTML = '请先选择用户';
        return;
    }
    const adminIds = users.filter(s => s.isAdmin).map(s => s.id);
    const targetIds = users.filter(s => !s.isAdmin).map(s => s.id);
    if(targetIds.length === 0){
        statusEl.innerHTML = '所选用户均为 admin，无法删除';
        return;
    }
    if(!confirm(`确认删除 ${targetIds.length} 个用户？（admin 将被跳过）`))
        return;
    statusEl.innerHTML = '删除中...';
    try {
        const res = await fetchWithAuth(
            `${window.APP_STATE.baseUrl}/users/delete`,
            {
                method:'POST',
                headers: Object.assign(
                    {'Content-Type':'application/json'}
                ),
                body: JSON.stringify({ user_ids: targetIds })
            }
        );
        const j = await res.json();
        if(!res.ok) {
            statusEl.innerHTML = '删除失败，' + Esc(j.message || '');
            return;
        }
        // 更新界面，移除对应条目
        const deleted_ids = j.deleted_ids || targetIds;
        deleted_ids.forEach(id => {
            const node = document.querySelector(`#users-results [data-user-id="${Esc(id)}"]`);
            if(node)
                node.remove();
        });
        statusEl.innerHTML = `已删除 ${deleted_ids.length} 个用户` + (adminIds.length ? `，${adminIds.length} 个管理员被跳过` : '');
    }
    catch(e) {
        statusEl.innerHTML = '删除异常：' + e;
    }
}

// 激活/冻结选中
async function SetActivateSelectedUsers(is_active = true)
{
    const users = CollectSelectedUsers();
    const statusEl = document.getElementById('users-action-status');
    statusEl.innerHTML = '';
    if(users.length === 0) {
        statusEl.innerHTML = '请先选择用户';
        return; 
    }
    let targetIds = users.map(s => s.id);
    const adminIds = users.filter(s => s.isAdmin).map(s => s.id);
    if(!is_active) {
        targetIds = users.filter(s => !s.isAdmin).map(s => s.id);
        if(targetIds.length === 0){
            statusEl.innerHTML = '所选用户均为 admin，无法冻结';
            return;
        }
    }
    if(!confirm(is_active ? `确认激活 ${targetIds.length} 个用户？` : `确认冻结 ${targetIds.length} 个用户？（admin 将被跳过）`))
        return;
    statusEl.innerHTML = '处理中...';
    try {
        const res = await fetchWithAuth(
            `${window.APP_STATE.baseUrl}/users/batch_update`,
            {
                method:'POST',
                headers: Object.assign(
                    {'Content-Type':'application/json'}
                ),
                body: JSON.stringify({ user_ids: targetIds, action: is_active ? 'activate' : 'freeze' })
            }
        );
        const j = await res.json();
        if(!res.ok) {
            statusEl.innerHTML = (is_active ? '激活失败，' : '冻结失败，') + Esc(j.message || '');
            return;
        }
        const updated_ids = j.updated_ids || ids;
        updated_ids.forEach(id => {
            const node = document.querySelector(`#users-results [data-user-id="${Esc(id)}"]`);
            if(node) {
                const right = node.querySelector('.text-right');
                if(right)
                    right.innerHTML = is_active ? 
                        `<span class="text-md text-green-600 font-medium">激活</span>` :
                        `<span class="text-md text-blue-600 font-medium">冻结</span>`;
            }
        });
        statusEl.innerHTML = is_active ? 
            `已激活 ${updated_ids.length} 个用户` :
            (`已冻结 ${updated_ids.length} 个用户` + (adminIds.length ? `，${adminIds.length} 个管理员被跳过` : ''));
    }
    catch(e) {
        statusEl.innerHTML = '异常：' + e;
    }
}

// 重置密码（默认 "12345678"）
async function ResetPasswordSelectedUsers(){
    const users = CollectSelectedUsers();
    const statusEl = document.getElementById('users-action-status');
    statusEl.innerHTML = '';
    if(users.length === 0) {
        statusEl.innerHTML = '请先选择用户';
        return;
    }
    const ids = users.map(s => s.id);
    if(!confirm(`确认将 ${ids.length} 个用户的密码重置为默认密码（12345678）？`))
        return;
    statusEl.innerHTML = '处理中...';
    try {
        const res = await fetchWithAuth(
            `${window.APP_STATE.baseUrl}/users/batch_update`,
            {
                method:'POST',
                headers: Object.assign(
                    {'Content-Type':'application/json'}
                ),
                body: JSON.stringify({ user_ids: ids, action: 'reset_password', password: '12345678' })
            }
        );
        const j = await res.json();
        if(!res.ok) {
            statusEl.innerHTML = '重置密码失败，' + Esc(j.message || '');
            return;
        }
        statusEl.innerHTML = `已重置 ${ (j.updated_ids || ids).length } 个用户的密码`;
    }
    catch(e) {
        statusEl.innerHTML = '重置密码异常：' + e;
    }
}

// 赋予或移除角色 (action = 'add' / 'remove')，无法变更用户的 admin 角色权限
async function ModifyRoleForSelected(action){
    const users = CollectSelectedUsers();
    const statusEl = document.getElementById('role-action-status');
    statusEl.innerHTML = '';
    if(users.length === 0) {
        statusEl.innerHTML = '请先选择用户';
        return;
    }
    const role = document.getElementById('role-select').value;
    if(!role) {
        statusEl.innerHTML = '请选择角色';
        return;
    }
    if(role == 'admin') {
        statusEl.innerHTML = '无法变更 admin 角色';
        return;
    }
    const ids = users.map(s => s.id);
    if(!confirm((action === 'add' ? `将赋予 ${ids.length} 个用户角色 "${role}"` : `将从 ${ids.length} 个用户移除角色 "${role}"`) + '，确认？'))
        return;
    return DoModifyRole(ids, role, action);
}

async function DoModifyRole(ids, role, action)
{
    const statusEl = document.getElementById('role-action-status');
    statusEl.innerHTML = '';
    statusEl.innerHTML = '处理中...';
    try {
        const res = await fetchWithAuth(
            `${window.APP_STATE.baseUrl}/users/batch_set_role`,
            {
                method:'POST',
                headers: Object.assign(
                    {'Content-Type':'application/json'}
                ),
                body: JSON.stringify({ user_ids: ids, role: role, action: action })
            }
        );
        const j = await res.json();
        if(!res.ok) {
            statusEl.innerHTML = '操作失败，' + Esc(j.message || '');
            return;
        }
        const updated_users = j.updated_users || [];
        if(Array.isArray(updated_users) && updated_users.length > 0) {
            updated_users.forEach(u => {
                const node = document.querySelector(`#users-results [data-user-id="${Esc(u.user_id)}"]`);
                if(node) {
                    node.setAttribute('data-roles', JSON.stringify(u.roles || []));
                    const roleArea = node.querySelector('div > div .mt-2 div.mt-1');
                    if(roleArea){
                        const rolesHtml = (u.roles && u.roles.length>0) ?
                            u.roles.map(r =>`<span class="inline-block px-2 py-0.5 mr-2 mb-1 text-sm bg-slate-100 rounded">${Esc(r)}</span>`).join('') :
                            '<span class="text-sm text-slate-400">无</span>';
                        roleArea.innerHTML = rolesHtml;
                    }
                }
            });
            statusEl.innerHTML = action === 'add' ? `已赋予 ${ids.length} 个用户角色 "${role}"` : `已移除 ${ids.length} 个用户的角色 "${role}"`;
        }
        else {
            statusEl.innerHTML = (action === 'add' ? `已赋予 ${ids.length} 个用户角色 "${role}"` : `已移除 ${ids.length} 个用户的角色 "${role}"`)
                + "，刷新后显示结果";
        }
    }
    catch(e) {
        statusEl.innerHTML = '异常：' + e;
    }
}
