import { fetchWithAuth } from './auth.js';

// manage.js - 数据管理页面逻辑
export function Initialize()
{
    // 导入按钮
    document.getElementById('btn-import-submit').addEventListener('click', Import);
    // 抓取按钮
    document.getElementById('btn-start-crawl').addEventListener('click',
        () => document.getElementById('crawl-status').textContent='状态：运行中');
    document.getElementById('btn-stop-crawl').addEventListener('click',
        () => document.getElementById('crawl-status').textContent='状态：已停止');
    // 查询按钮
    document.getElementById('btn-search-posts').addEventListener('click', Query);
    // 管理按钮
    document.getElementById('btn-select-all').addEventListener('click',
        () => document.querySelectorAll('#posts-results .post-checkbox').forEach(cb => cb.checked = true));
    document.getElementById('btn-select-none').addEventListener('click',
        () => document.querySelectorAll('#posts-results .post-checkbox').forEach(cb => cb.checked = false));
    document.getElementById('btn-delete-selected').addEventListener('click', DeleteSelectedPosts);
    document.getElementById('btn-delete-all').addEventListener('click', DeleteAllPosts);
    document.getElementById('btn-reanalyze-selected').addEventListener('click', ReanalyzeSelectedPosts);
    document.getElementById('btn-reanalyze-all').addEventListener('click', ReanalyzeAllPosts);
    document.getElementById('btn-delete-sentiments-selected').addEventListener('click', DeleteSelectedSentiments);
    document.getElementById('btn-delete-sentiments-all').addEventListener('click', DeleteAllSentiments);
    // 翻页按钮
    document.getElementById('prev-page').addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            renderPostsPage(window.posts, currentPage);
        }
    });
    document.getElementById('next-page').addEventListener('click', () => {
        const totalPages = Math.ceil(window.posts.length / postsPerPage);
        if (currentPage < totalPages) {
            currentPage++;
            renderPostsPage(window.posts, currentPage);
        }
    });
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

// 提取查询参数
function BuildParams()
{
    const params = new URLSearchParams();
    const ids = document.getElementById('q-ids')?.value || ''; 
    const s = document.getElementById('q-start')?.value || ''; 
    const e = document.getElementById('q-end')?.value || ''; 
    const ts = document.getElementById('q-topics')?.value || ''; 
    const ks = document.getElementById('q-keywords')?.value || ''; 
    const p = document.getElementById('q-platform').value; 
    const m = document.getElementById('q-model').value;
    const t = document.getElementById('q-type').value;
    if(ids)
        params.set('post_ids', ids);
    if(s)
        params.set('start_time', s);
    if(e)
        params.set('end_time', e);
    if(ts)
        params.set('topics', ts);
    if(ks)
        params.set('keywords', ks);
    if(p) 
        params.set('platform', p); 
    if(m)
        params.set('model', m);
    if(t) 
        params.set('type', t);
    return params;
}

// 渲染单页
const postsPerPage = 100;
let currentPage = 1;
function renderPostsPage(posts, page = 1) {
    const container = document.getElementById('posts-results');
    container.innerHTML = '';
    const start = (page - 1) * postsPerPage;
    const end = start + postsPerPage;
    const pagePosts = posts.slice(start, end);
    pagePosts.forEach(post => {
        const div = document.createElement('div');
        div.className = "bg-white shadow-md rounded-xl p-4 mb-4 border border-gray-200 hover:shadow-lg transition";
        div.setAttribute('data-post-id', post.post_id);
        const sentimentDisplay = GenerateSentimentDisplay(post.sentiments);
        div.innerHTML = `
            <div class="flex posts-start">
                <input type="checkbox" 
                    class="mt-1 mr-3 h-5 w-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500 post-checkbox" 
                    data-post-id="${Esc(post.post_id)}">
                <div class="flex-1">
                    <p class="text-sm text-gray-500"><b>POST ID:</b> ${Esc(post.post_id)}</p>
                    <p class="text-sm text-gray-500"><b>平台:</b> ${Esc(post.platform)}</p>
                    <p class="text-sm text-gray-500"><b>发布者:</b> ${Esc(post.username)}</p>
                    <p class="text-sm text-gray-500"><b>位置:</b> ${Esc(post.location) || '未知'}</p>
                    <p class="mt-2 text-gray-800"><b>内容:</b> ${Esc(post.content)}</p>
                    <p class="mt-1 text-xs text-gray-400"><b>时间:</b> ${Esc(post.create_time)}</p>
                    <p class="mt-2 text-sm text-slate-600"><b>情感分析记录:</b></p>
                    <div class="post-sentiments">
                        ${sentimentDisplay}
                    </div>
                </div>
            </div>
        `;
        container.appendChild(div);
    });
    // 更新页码信息
    const pageInfo = document.getElementById('page-info');
    const totalPages = Math.ceil(posts.length / postsPerPage);
    pageInfo.textContent = `第 ${page} / ${totalPages} 页`;
    // 控制按钮状态
    document.getElementById('prev-page').disabled = (page === 1);
    document.getElementById('next-page').disabled = (page === totalPages);
    if(posts.length <= 0)
        container.innerHTML = '未查询到相关数据';
}

// 生成单条帖子的情感分析结果列表
function GenerateSentimentDisplay(sentiments)
{
    var sentimentDisplay = '无';
    if (sentiments && Array.isArray(sentiments) && sentiments.length > 0) {
        sentimentDisplay = `
            <table class="mt-2 text-sm text-gray-700 border border-gray-200 rounded w-full">
                <thead class="bg-gray-100">
                    <tr>
                        <th class="px-2 py-1 text-left">模型</th>
                        <th class="px-2 py-1 text-left">情感</th>
                        <th class="px-2 py-1 text-left">分数</th>
                        <th class="px-2 py-1 text-left">分析时间</th>
                    </tr>
                </thead>
                <tbody>
                    ${sentiments.map(m => `
                        <tr class="border-t">
                            <td class="px-2 py-1">${Esc(m.model)}</td>
                            <td class="px-2 py-1">${Esc(m.type)}</td>
                            <td class="px-2 py-1">${Esc(m.score)}</td>
                            <td class="px-2 py-1">${Esc(m.analysis_time)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }
    return sentimentDisplay;
}

// 渲染查询结果
function RenderPosts(posts)
{
    document.getElementById('posts-list-title').innerHTML = `查询结果（共 ${posts.length} 条记录，每页显示 ${postsPerPage} 条）`;
    window.posts = posts;
    currentPage = 1;
    renderPostsPage(posts, currentPage);
}

// 获得勾选的帖子id
function CollectSelectedPostIds()
{
    const checks = Array.from(document.querySelectorAll('#posts-results .post-checkbox:checked'));
    const ids = checks.map(c => c.getAttribute('data-post-id')).filter(Boolean);
    return ids;
}

/* ---------- 
- 按钮事件函数
----------  */

// 导入
async function Import()
{
    const f = document.getElementById('import-file');
    const statusEl = document.getElementById('import-status');
    if(!f.files.length) {
        statusEl.innerHTML = '请选择文件';
        return;
    }
    const fd = new FormData();
    fd.append('file', f.files[0]);
    fd.append('platform', document.getElementById('import-platform').value);
    document.querySelectorAll('.model-checkbox:checked').forEach(cb => fd.append('models[]', cb.value));
    statusEl.innerHTML = '上传中...';
    try {
        const res = await fetchWithAuth(
            `${window.APP_STATE.baseUrl}/posts/import`,
            {
                method:'POST',
                headers: {},
                body: fd
            }
        );
        const j = await res.json();
        if(res.ok)
            statusEl.innerHTML = '导入成功';
        else
            statusEl.innerHTML = '导入失败，' + Esc(j.message || '');
    }
    catch(e){
        statusEl.innerHTML='导入异常：' + e;
    }
}

// 查询并渲染
async function Query()
{ 
    document.getElementById('q-panel').classList.remove('hidden');
    document.getElementById('manage-status').innerHTML = '';
    document.getElementById('reanalyze-status').innerHTML = '';
    const params = BuildParams()
    const container = document.getElementById('posts-results'); 
    container.innerHTML = '查询中...'; 
    try {
        const res = await fetchWithAuth(
            `${window.APP_STATE.baseUrl}/posts/query${params.toString() ? '?' + params.toString() : ''}`,
            {headers: {}}
        );
        const j = await res.json();
        if(!res.ok) { 
            container.innerHTML = '查询失败，' + Esc(j.message || ''); 
            return; 
        } 
        const posts = j.posts || [];
        RenderPosts(posts);
    }
    catch(e) { 
        container.innerHTML = '查询异常：' + e; 
    } 
} 

// 删除选中
async function DeleteSelectedPosts()
{ 
    const container = document.getElementById('posts-results');
    const ids = CollectSelectedPostIds();
    const statusEl = document.getElementById('manage-status');
    if(!ids || ids.length === 0){
        statusEl.innerHTML = '请选择需要删除的帖子';
        return;
    }
    if(!confirm(`确认删除 ${ids.length} 条记录？ 此操作不可撤销。`))
        return;
    statusEl.innerHTML = '删除中...';
    try {
        const res = await fetchWithAuth(
            `${window.APP_STATE.baseUrl}/posts/delete`,
            {
                method: 'POST',
                headers: Object.assign(
                    {'Content-Type':'application/json'}
                ),
                body: JSON.stringify({ post_ids: ids })
            }
        );
        const j = await res.json();
        if(!res.ok){
            statusEl.innerHTML = '删除失败，' + Esc(j.message || '');
            return;
        }
        // 更新界面，移除对应条目
        const deleted_ids = (j.deleted_ids ? j.deleted_ids : ids)
        deleted_ids.forEach(id => {
            const node = document.querySelector(`#posts-results [data-post-id="${Esc(id)}"]`);
            if(node)
                node.remove();
        });
        // 更新window.posts数组
        window.posts = window.posts.filter(post => !deleted_ids.includes(post.post_id));
        // 重新渲染页面
        const totalPages = Math.ceil(window.posts.length / postsPerPage);
        if (currentPage > totalPages) {
            currentPage = totalPages || 1;
        }
        renderPostsPage(window.posts, currentPage);
        statusEl.innerHTML = `已删除 ${deleted_ids.length} 条记录`;
    }
    catch(e) {
        statusEl.innerHTML = '删除异常：' + e;
    }
}

// 删除所有查询结果
async function DeleteAllPosts()
{
    const statusEl = document.getElementById('manage-status');
    if (!window.posts || window.posts.length === 0) {
        statusEl.innerHTML = '没有查询到数据，无法删除';
        return;
    }
    const ids = window.posts.map(p => p.post_id);
    if (!confirm(`确认删除所有 ${ids.length} 条查询结果？ 此操作不可撤销。`)) {
        return;
    }
    statusEl.innerHTML = '删除中...';
    try {
        const res = await fetchWithAuth(
            `${window.APP_STATE.baseUrl}/posts/delete`,
            {
                method: 'POST',
                headers: Object.assign({'Content-Type': 'application/json'}),
                body: JSON.stringify({ post_ids: ids })
            }
        );
        const j = await res.json();
        if (!res.ok) {
            statusEl.innerHTML = '删除失败，' + Esc(j.message || '');
            return;
        }
        // 更新window.posts数组
        window.posts = [];
        // 重新渲染页面
        currentPage = 1;
        renderPostsPage(window.posts, currentPage);
        statusEl.innerHTML = `已删除所有 ${ids.length} 条记录`;
    }
    catch (e) {
        statusEl.innerHTML = '删除异常：' + e;
    }
}

// 对全部 posts 用所选模型进行情感分析
async function ReanalyzeAllPosts()
{
    if (!window.posts || window.posts.length === 0) {
        document.getElementById('reanalyze-status').innerHTML = '没有查询到数据，无法分析';
        return;
    }
    const ids = window.posts.map(p => p.post_id);
    const model = document.getElementById('reanalyze-model').value;
    if (!model) {
        document.getElementById('reanalyze-status').innerHTML = '请选择一个模型';
        return;
    }
    if(!confirm(`确定对所有 ${ids.length} 条查询结果使用模型 "${model}" 进行情感分析，并更新数据库吗？`))
        return;
    const statusEl = document.getElementById('reanalyze-status');
    statusEl.innerHTML = '处理中...';
    try {
        const res = await fetchWithAuth(
            `${window.APP_STATE.baseUrl}/posts/reanalyze`, 
            {
                method: 'POST',
                headers: Object.assign({'Content-Type':'application/json'}),
                body: JSON.stringify({ post_ids: ids, model: model })
            }
        );
        const j = await res.json();
        if(!res.ok) {
            statusEl.innerHTML = '分析失败，' + Esc(j.message || '');
            return;
        }
        // 更新对应条目
        if (j && j.analyzed_posts) {
            j.analyzed_posts.forEach(post => {
                const sentimentDisplay = GenerateSentimentDisplay(post.sentiments)
                const card = document.querySelector(`#posts-results [data-post-id="${post.post_id}"]`);
                if (card) {
                    const sentimentContainer = card.querySelector('.post-sentiments');
                    if (sentimentContainer) {
                        sentimentContainer.innerHTML = sentimentDisplay;
                    }
                }
            });
            statusEl.innerHTML = '情感分析并更新成功';
        }
        else {
            statusEl.innerHTML = '情感分析成功，刷新后显示结果';
        }
    }
    catch(e) {
        statusEl.innerHTML = '分析异常：' + e;
    }
}

// 删除全部的指定模型的情感记录
async function DeleteAllSentiments()
{
    if (!window.posts || window.posts.length === 0) {
        document.getElementById('reanalyze-status').innerHTML = '没有查询到数据，无法删除';
        return;
    }
    const ids = window.posts.map(p => p.post_id);
    const model = document.getElementById('reanalyze-model').value;
    if (!model) {
        document.getElementById('reanalyze-status').innerHTML = '请选择一个模型';
        return;
    }
    if(!confirm(`确定删除所有 ${ids.length} 条查询结果在模型 "${model}" 下的情感分析结果，并更新数据库吗？`))
        return;
    const statusEl = document.getElementById('reanalyze-status');
    statusEl.innerHTML = '处理中...';
    try {
        const res = await fetchWithAuth(
            `${window.APP_STATE.baseUrl}/posts/delete_sentiments`, 
            {
                method: 'POST',
                headers: Object.assign({'Content-Type':'application/json'}),
                body: JSON.stringify({ post_ids: ids, model: model })
            }
        );
        const j = await res.json();
        if(!res.ok){
            statusEl.innerHTML = '删除失败，' + Esc(j.message || '');
            return;
        }
        // 更新对应条目
        if (j && j.updated_posts) {
            j.updated_posts.forEach(post => {
                const sentimentDisplay = GenerateSentimentDisplay(post.sentiments)
                const card = document.querySelector(`#posts-results [data-post-id="${post.post_id}"]`);
                if (card) {
                    const sentimentContainer = card.querySelector('.post-sentiments');
                    if (sentimentContainer) {
                        sentimentContainer.innerHTML = sentimentDisplay;
                    }
                }
            });
            statusEl.innerHTML = '情感分析结果删除成功';
        }
        else {
            statusEl.innerHTML = '情感分析结果删除成功，刷新后显示结果';
        }
    }
    catch(e) {
        statusEl.innerHTML = '删除异常：' + e;
    }
}

// 对选中 posts 用所选模型进行情感分析
async function ReanalyzeSelectedPosts()
{
    const ids = CollectSelectedPostIds();
    const statusEl = document.getElementById('reanalyze-status');
    if (!ids || ids.length === 0) {
        statusEl.innerHTML = '请选择需要分析的帖子';
        return;
    }
    const model = document.getElementById('reanalyze-model').value;
    if (!model) {
        statusEl.innerHTML = '请选择一个模型';
        return;
    }
    if(!confirm(`确定对 ${ids.length} 条选中记录使用模型 "${model}" 进行情感分析，并更新数据库吗？`))
        return;
    statusEl.innerHTML = '处理中...';
    try {
        const res = await fetchWithAuth(
            `${window.APP_STATE.baseUrl}/posts/reanalyze`, 
            {
                method: 'POST',
                headers: Object.assign({'Content-Type':'application/json'}),
                body: JSON.stringify({ post_ids: ids, model: model })
            }
        );
        const j = await res.json();
        if(!res.ok) {
            statusEl.innerHTML = '分析失败，' + Esc(j.message || '');
            return;
        }
        // 更新对应条目
        if (j && j.analyzed_posts) {
            j.analyzed_posts.forEach(post => {
                const sentimentDisplay = GenerateSentimentDisplay(post.sentiments)
                const card = document.querySelector(`#posts-results [data-post-id="${post.post_id}"]`);
                if (card) {
                    const sentimentContainer = card.querySelector('.post-sentiments');
                    if (sentimentContainer) {
                        sentimentContainer.innerHTML = sentimentDisplay;
                    }
                }
            });
            statusEl.innerHTML = '情感分析并更新成功';
        }
        else {
            statusEl.innerHTML = '情感分析成功，刷新后显示结果';
        }
    }
    catch(e) {
        statusEl.innerHTML = '分析异常：' + e;
    }
}

// 删除选中的指定模型的情感记录
async function DeleteSelectedSentiments()
{
    const ids = CollectSelectedPostIds();
    const statusEl = document.getElementById('reanalyze-status');
    if (!ids || ids.length === 0) {
        statusEl.innerHTML = '请选择需要删除分析记录的帖子';
        return;
    }
    const model = document.getElementById('reanalyze-model').value;
    if (!model) {
        statusEl.innerHTML = '请选择一个模型';
        return;
    }
    if(!confirm(`确定删除 ${ids.length} 条选中记录在模型 "${model}" 下的情感分析结果，并更新数据库吗？`))
        return;
    statusEl.innerHTML = '处理中...';
    try {
        const res = await fetchWithAuth(
            `${window.APP_STATE.baseUrl}/posts/delete_sentiments`, 
            {
                method: 'POST',
                headers: Object.assign({'Content-Type':'application/json'}),
                body: JSON.stringify({ post_ids: ids, model: model })
            }
        );
        const j = await res.json();
        if(!res.ok){
            statusEl.innerHTML = '删除失败，' + Esc(j.message || '');
            return;
        }
        // 更新对应条目
        if (j && j.updated_posts) {
            j.updated_posts.forEach(post => {
                const sentimentDisplay = GenerateSentimentDisplay(post.sentiments)
                const card = document.querySelector(`#posts-results [data-post-id="${post.post_id}"]`);
                if (card) {
                    const sentimentContainer = card.querySelector('.post-sentiments');
                    if (sentimentContainer) {
                        sentimentContainer.innerHTML = sentimentDisplay;
                    }
                }
            });
            statusEl.innerHTML = '情感分析结果删除成功';
        }
        else {
            statusEl.innerHTML = '情感分析结果删除成功，刷新后显示结果';
        }
    }
    catch(e) {
        statusEl.innerHTML = '删除异常：' + e;
    }
}
