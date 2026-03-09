import { fetchWithAuth } from './auth.js';

export function Initialize()
{
    document.getElementById('btn-query').addEventListener('click', Query);
    document.getElementById('btn-clear').addEventListener('click', ClearPostResults);
    document.getElementById('btn-export').addEventListener('click', ExportCSV);
    document.getElementById('btn-show-sentiment').addEventListener('click', ShowSentiment);
    document.getElementById('btn-show-topics').addEventListener('click', () => ShowWords('topics'));
    document.getElementById('btn-show-keywords').addEventListener('click', () => ShowWords('keywords'));
    document.getElementById('btn-show-heatmap').addEventListener('click', ShowHeatmap);
    document.getElementById('btn-show-time-trend').addEventListener('click', ShowTimeTrend);
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
    const s = document.getElementById('q-start')?.value || ''; 
    const e = document.getElementById('q-end')?.value || ''; 
    const ts = document.getElementById('q-topics')?.value || ''; 
    const ks = document.getElementById('q-keywords')?.value || ''; 
    const p = document.getElementById('q-platform').value; 
    const m = document.getElementById('q-model').value;
    const t = document.getElementById('q-type').value;
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

function HideVisuals()
{
    document.getElementById('visualize-status').innerHTML = '';
    ['sentiment-chart-card','time-trend-card','topic-card','keywords-card','heatmap-card'].forEach(id => {
        const el = document.getElementById(id);
        if(el)
            el.classList.add('hidden');
    });
}

/* ---------- 
- 按钮事件函数
----------  */

// 查询并渲染
async function Query()
{
    document.getElementById('posts-list').classList.remove('hidden');
    HideVisuals();
    const params = BuildParams();
    const container = document.getElementById('posts-results');
    container.innerHTML = '查询中...';
    try {
        const res = await fetchWithAuth(
            `${window.APP_STATE.baseUrl}/posts/query${params.toString() ? '?' + params.toString() : ''}`,
            {headers:{}}
        );
        const j = await res.json();
        if(!res.ok){
            container.innerHTML = '查询失败：' + j.message; 
            return;
        }
        const posts = j.posts || []; 
        RenderPosts(posts);
        window._last_query_results = posts;
    }
    catch(e) { 
        container.innerHTML = '查询异常：' + e; 
    } 
}

// 导出 CSV
async function ExportCSV(){
    const params = BuildParams();
    try {
        const res = await fetchWithAuth(
            `${window.APP_STATE.baseUrl}/posts/export${params.toString() ? '?' + params.toString() : ''}`,
            {headers:{}}
        );
        if(!res.ok){
            const j = await res.json();
            alert('导出失败，' + j.message);
            return;
        }
        const blob = await res.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = "export.csv";
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(downloadUrl);
    }
    catch(e) { 
        alert("导出异常：" + e);
    } 
}

// 清空查询结果
function ClearPostResults()
{
    document.getElementById('posts-results').innerHTML = '';
    document.getElementById('posts-list').classList.add('hidden');
    document.getElementById('sentiment-chart-card').classList.add('hidden');
    document.getElementById('time-trend-card').classList.add('hidden');
    document.getElementById('topics-card').classList.add('hidden');
    document.getElementById('keywords-card').classList.add('hidden');
    document.getElementById('heatmap-card').classList.add('hidden');
    window._last_query_results = null;
    HideVisuals();
}

/* ---------- 
- 可视化功能
----------  */

// 情感分布
async function ShowSentiment()
{
    const params = BuildParams();
    const statusEl = document.getElementById('visualize-status');
    statusEl.innerHTML = '情感分布生成中...';
    try {
        const res = await fetchWithAuth(
            `${window.APP_STATE.baseUrl}/visual/sentiment_distribution${params.toString() ? '?' + params.toString() : ''}`,
            {headers:{}}
        );
        const j = await res.json();
        if (!res.ok) {
            statusEl.innerHTML = '获取情感分布失败，' + Esc(j.message || '');
            return;
        }
        const counts = j.counts || {};
        // expect counts: [{'positive': 24}, {'neutral': 18}, {'negativ': 27}, ]
        RenderSentimentChart(counts);
        statusEl.innerHTML = '生成情感分布成功';
    }
    catch(e) {
        statusEl.innerHTML = '错误: ' + e;
    }
}

let _sentimentChart = null;
function RenderSentimentChart(counts)
{
    const card = document.getElementById('sentiment-chart-card');
    card.classList.remove('hidden');
    const ctx = document.getElementById('sentiment-chart').getContext('2d');
    if(_sentimentChart)
        _sentimentChart.destroy();
    // 样式设置
    const keys = ['positive', 'neutral', 'negative'];
    const colorMap = {
        positive: '#288ae5',
        neutral: '#acf524',
        negative: '#f06363'
    };
    const labels = keys;
    const data = labels.map(l => counts[l] || 0);
    const colors = labels.map(l => colorMap[l]);
    _sentimentChart = new Chart(ctx, {
        type: 'doughnut',
        data: { labels, datasets: [{ data, backgroundColor: colors }] },
        options: { responsive:true, maintainAspectRatio:false }
    });
}

// 关键词热度 / 话题热度
async function ShowWords(mode="keywords")
{
    const params = BuildParams();
    const statusEl = document.getElementById('visualize-status');
    statusEl.innerHTML = (mode === "keywords" ? '关键词热度生成中...' : '话题热度生成中...');
    try {
        const maxWords = document.getElementById(mode === "keywords" ? 'wc-max-keywords' : 'wc-max-topics').value || 20;
        if(maxWords < 1 || maxWords > 100)
            maxWords = 20;
        // 获取词分布
        const res = await fetchWithAuth(
            `${window.APP_STATE.baseUrl}/visual/top_words${params.toString() ? '?' + params.toString() + '&' : '?'}max_words=${maxWords}&mode=${mode}`,
            {headers:{}}
        );
        const j = await res.json();
        if(!res.ok) {
            statusEl.innerHTML = (mode === "keywords" ? '生成关键词热度失败，' : '生成话题热度失败，') + Esc(j.message || '');
            return;
        }
        const counts = j.counts || [];
        // expect counts: [['keyword1', 12], ['keyword2', 9], ...]
        RenderKeywordsChart(counts, mode);
        // 获取词云图片
        const wcRes = await fetchWithAuth(
            `${window.APP_STATE.baseUrl}/visual/wordcloud${params.toString() ? '?' + params.toString() + '&' : '?'}max_words=${maxWords}&mode=${mode}`,
            {headers:{}}
        );
        if(wcRes.ok) {
            const blob = await wcRes.blob();
            const url = URL.createObjectURL(blob);
            const img = document.getElementById(mode === "keywords" ? 'keyword-wordcloud-img' : 'topic-wordcloud-img');
            img.src = url;
            img.classList.remove('hidden');
            document.getElementById(mode === "keywords" ? 'keywords-card' : 'topics-card').classList.remove('hidden');
        }
        statusEl.innerHTML = (mode === "keywords" ? '生成关键词分布和词云成功' : '生成话题分布和词云成功');
    }
    catch(e) {
        statusEl.innerHTML = '错误: ' + e;
    }
}

let _keywordsChart = null;
let _topicsChart = null;
function RenderKeywordsChart(counts, mode="keywords")
{
    let card;
    let ctx;
    if(mode === "keywords") {
        card = document.getElementById('keywords-card');
        ctx = document.getElementById('keywords-chart').getContext('2d');
        if(_keywordsChart)
            _keywordsChart.destroy();
    }
    else if(mode === "topics") {
        card = document.getElementById('topics-card');
        ctx = document.getElementById('topics-chart').getContext('2d');
        if(_topicsChart)
            _topicsChart.destroy();
    }
    else
        return;
    const labels = counts.map(k => k[0]);
    const data = counts.map(k => k[1]);
    card.classList.remove('hidden');
    const chart = new Chart(ctx, {
        type: 'bar',
        data: { labels, datasets: [{ label:'频次', data }] },
        options: { responsive:true, maintainAspectRatio:false }
    });
    if(mode === "keywords")
        _keywordsChart = chart;
    else if(mode === "topics")
        _topicsChart = chart;
}

// 时间趋势
async function ShowTimeTrend()
{
    const params = BuildParams();
    const statusEl = document.getElementById('visualize-status');
    statusEl.innerHTML = '时间趋势生成中...';
    try {
        const res = await fetchWithAuth(
            `${window.APP_STATE.baseUrl}/visual/sentiment_trend${params.toString() ? '?' + params.toString() : ''}`,
            {headers:{}}
        );
        const j = await res.json();
        if(!res.ok) {
            statusEl.innerHTML = '获取时间趋势失败，' + Esc(j.message || '');
            return;
        }
        const trendData = j.trendData
        // expect trendData: {dates: ['2025-09-01','2025-09-02',...], positive: [...], neutral: [...], negative: [...]}
        RenderTimeTrend(trendData);
        statusEl.innerHTML = '生成情感时间趋势成功';
    }
    catch(e){
        alert('错误: ' + e);
    }
}

let _timeTrendChart = null;
function RenderTimeTrend(data)
{
    const card = document.getElementById('time-trend-card');
    card.classList.remove('hidden');
    const ctx = document.getElementById('time-trend-chart').getContext('2d');
    if(_timeTrendChart) _timeTrendChart.destroy();
    _timeTrendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.dates,
            datasets: [
                { label:'positive', data:data.positive, borderColor:'#288ae5', fill:false },
                { label:'neutral', data:data.neutral, borderColor:'#acf524', fill:false },
                { label:'negative', data:data.negative, borderColor:'#f06363', fill:false }
            ]
        },
        options: { responsive:true, maintainAspectRatio:false }
    });
}

// 热力图
async function ShowHeatmap()
{
    const params = BuildParams();
    const statusEl = document.getElementById('visualize-status');
    statusEl.innerHTML = '生成中...（由于地理 API 访问限制，生成速度可能较慢，请耐心等待）';
    try {
        const res = await fetchWithAuth(
            `${window.APP_STATE.baseUrl}/visual/heatmap${params.toString() ? '?' + params.toString() : ''}`,
            {headers:{}}
        );
            if(!res.ok) {
            const j = await res.json();
            statusEl.innerHTML = '生成情感分布热力图失败，' + j.message;
            return;
        }
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        document.getElementById('map-iframe').src = url;
        document.getElementById('heatmap-card').classList.remove('hidden');
        statusEl.innerHTML = '生成情感分布热力图成功';
    }
    catch(e) {
        statusEl.innerHTML = '错误: ' + e;
    }
}