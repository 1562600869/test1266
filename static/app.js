const API_BASE = '';
let config = { age_groups: [], positions: [], camp_statuses: [] };
let players = [];
let camps = [];

async function api(url, method = 'GET', body = null) {
    const options = {
        method,
        headers: { 'Content-Type': 'application/json' }
    };
    if (body) options.body = JSON.stringify(body);
    const res = await fetch(API_BASE + url, options);
    return await res.json();
}

function showToast(message, isError = false) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = 'toast ' + (isError ? 'error' : 'success');
    setTimeout(() => toast.classList.add('hidden'), 3000);
}

function formatDateTime(s) {
    if (!s) return '-';
    return s.replace('T', ' ').substring(0, 19);
}

function getStatusClass(status) {
    if (status === '报名中') return 'status-open';
    if (status === '进行中') return 'status-active';
    return 'status-closed';
}

async function loadConfig() {
    config = await api('/api/config');
    populateSelect('playerForm select[name="age_group"]', config.age_groups);
    populateSelect('playerForm select[name="position"]', config.positions);
    populateSelect('campForm select[name="status"]', config.camp_statuses);
}

function populateSelect(selector, options) {
    const sel = document.querySelector(selector);
    if (!sel) return;
    const first = sel.options[0];
    sel.innerHTML = '';
    if (first) sel.appendChild(first.cloneNode(true));
    options.forEach(v => {
        const opt = document.createElement('option');
        opt.value = v;
        opt.textContent = v;
        sel.appendChild(opt);
    });
}

function populatePlayerSelects() {
    ['registerForm select[name="player_id"]', 'checkinForm select[name="player_id"]', 'playerCheckinForm select[name="player_id"]'].forEach(sel => {
        const s = document.querySelector(sel);
        if (!s) return;
        const first = s.options[0];
        s.innerHTML = '';
        if (first) s.appendChild(first.cloneNode(true));
        players.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.id;
            opt.textContent = `${p.nickname} (${p.age_group})`;
            s.appendChild(opt);
        });
    });
}

function populateCampSelects() {
    const regSel = document.querySelector('registerForm select[name="camp_id"]');
    if (regSel) {
        const first = regSel.options[0];
        regSel.innerHTML = '';
        if (first) regSel.appendChild(first.cloneNode(true));
        camps.filter(c => c.status === '报名中').forEach(c => {
            const opt = document.createElement('option');
            opt.value = c.id;
            opt.textContent = `${c.name} (${c.registered_count}/${c.max_capacity})`;
            regSel.appendChild(opt);
        });
    }

    const ciSel = document.querySelector('checkinForm select[name="camp_id"]');
    if (ciSel) {
        const first = ciSel.options[0];
        ciSel.innerHTML = '';
        if (first) ciSel.appendChild(first.cloneNode(true));
        camps.filter(c => c.status === '进行中').forEach(c => {
            const opt = document.createElement('option');
            opt.value = c.id;
            opt.textContent = c.name;
            ciSel.appendChild(opt);
        });
    }
}

async function loadPlayers() {
    players = await api('/api/players');
    const tbody = document.querySelector('#playersTable tbody');
    tbody.innerHTML = '';
    for (const p of players) {
        const mc = await api(`/api/player/${p.id}/checkins/month`);
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${p.id}</td>
            <td>${p.nickname}</td>
            <td>${p.phone}</td>
            <td>${p.age_group}</td>
            <td>${p.position}</td>
            <td>${mc.count}</td>
            <td>
                <button class="btn-sm btn-primary" onclick="editPlayer(${p.id})">编辑</button>
                <button class="btn-sm btn-danger" onclick="deletePlayer(${p.id})">删除</button>
            </td>
        `;
        tbody.appendChild(tr);
    }
    populatePlayerSelects();
}

async function loadCamps() {
    camps = await api('/api/camps');
    const tbody = document.querySelector('#campsTable tbody');
    tbody.innerHTML = '';
    camps.forEach(c => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${c.id}</td>
            <td>${c.name}</td>
            <td>${c.start_date}</td>
            <td>${c.end_date}</td>
            <td>${c.fee}</td>
            <td>${c.max_capacity}</td>
            <td>${c.registered_count}</td>
            <td><span class="status ${getStatusClass(c.status)}">${c.status}</span></td>
            <td>
                <button class="btn-sm btn-primary" onclick="editCamp(${c.id})">编辑</button>
                <button class="btn-sm btn-danger" onclick="deleteCamp(${c.id})">删除</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
    populateCampSelects();
}

async function loadRegistrations() {
    const regs = await api('/api/registrations');
    const tbody = document.querySelector('#registrationsTable tbody');
    tbody.innerHTML = '';
    regs.forEach(r => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${r.id}</td>
            <td>${r.nickname}</td>
            <td>${r.age_group}</td>
            <td>${r.camp_name}</td>
            <td>${formatDateTime(r.created_at)}</td>
        `;
        tbody.appendChild(tr);
    });
}

async function loadCheckins() {
    const cis = await api('/api/checkins');
    const tbody = document.querySelector('#checkinsTable tbody');
    tbody.innerHTML = '';
    cis.forEach(c => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${c.id}</td>
            <td>${c.nickname}</td>
            <td>${c.age_group}</td>
            <td>${c.camp_name}</td>
            <td>${c.checkin_date}</td>
            <td>${formatDateTime(c.created_at).split(' ')[1]}</td>
        `;
        tbody.appendChild(tr);
    });
}

async function loadStats() {
    const stats = await api('/api/stats/registrations/monthly');
    const container = document.getElementById('ageGroupStats');
    container.innerHTML = `<p class="stat-month">${stats.month}</p>`;
    const table = document.createElement('table');
    table.className = 'stats-table';
    let total = 0;
    for (const [age, count] of Object.entries(stats.stats)) {
        total += count;
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${age}</td><td>${count} 人次</td>`;
        table.appendChild(tr);
    }
    const tr = document.createElement('tr');
    tr.innerHTML = `<td><strong>合计</strong></td><td><strong>${total} 人次</strong></td>`;
    table.appendChild(tr);
    container.appendChild(table);
}

function openModal(title, fields, onSubmit) {
    document.getElementById('modalTitle').textContent = title;
    const fieldsDiv = document.getElementById('modalFields');
    fieldsDiv.innerHTML = '';
    fields.forEach(f => {
        const div = document.createElement('div');
        div.className = 'form-group';
        if (f.type === 'select') {
            div.innerHTML = `<label>${f.label}</label><select name="${f.name}" required></select>`;
            const sel = div.querySelector('select');
            f.options.forEach(v => {
                const opt = document.createElement('option');
                opt.value = v;
                opt.textContent = v;
                if (v === f.value) opt.selected = true;
                sel.appendChild(opt);
            });
        } else {
            div.innerHTML = `<label>${f.label}</label><input type="${f.type}" name="${f.name}" value="${f.value || ''}" required>`;
        }
        fieldsDiv.appendChild(div);
    });
    document.getElementById('modal').classList.remove('hidden');
    document.getElementById('modalForm').onsubmit = (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = {};
        formData.forEach((v, k) => data[k] = v);
        onSubmit(data);
        closeModal();
    };
}

function closeModal() {
    document.getElementById('modal').classList.add('hidden');
}

function editPlayer(id) {
    const p = players.find(x => x.id === id);
    if (!p) return;
    openModal('编辑球员', [
        { label: '昵称', name: 'nickname', type: 'text', value: p.nickname },
        { label: '手机', name: 'phone', type: 'tel', value: p.phone },
        { label: '年龄组', name: 'age_group', type: 'select', options: config.age_groups, value: p.age_group },
        { label: '位置', name: 'position', type: 'select', options: config.positions, value: p.position }
    ], async (data) => {
        await api(`/api/players/${id}`, 'PUT', data);
        showToast('更新成功');
        loadPlayers();
    });
}

async function deletePlayer(id) {
    if (!confirm('确定删除该球员？')) return;
    await api(`/api/players/${id}`, 'DELETE');
    showToast('删除成功');
    loadPlayers();
}

function editCamp(id) {
    const c = camps.find(x => x.id === id);
    if (!c) return;
    openModal('编辑营期', [
        { label: '名称', name: 'name', type: 'text', value: c.name },
        { label: '开始日期', name: 'start_date', type: 'date', value: c.start_date },
        { label: '结束日期', name: 'end_date', type: 'date', value: c.end_date },
        { label: '费用(分)', name: 'fee', type: 'number', value: c.fee },
        { label: '最大人数', name: 'max_capacity', type: 'number', value: c.max_capacity },
        { label: '状态', name: 'status', type: 'select', options: config.camp_statuses, value: c.status }
    ], async (data) => {
        await api(`/api/camps/${id}`, 'PUT', data);
        showToast('更新成功');
        loadCamps();
    });
}

async function deleteCamp(id) {
    if (!confirm('确定删除该营期？')) return;
    await api(`/api/camps/${id}`, 'DELETE');
    showToast('删除成功');
    loadCamps();
}

document.addEventListener('DOMContentLoaded', async () => {
    await loadConfig();
    await Promise.all([loadPlayers(), loadCamps(), loadRegistrations(), loadCheckins(), loadStats()]);

    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(btn.dataset.tab).classList.add('active');
            if (btn.dataset.tab === 'register') loadRegistrations();
            if (btn.dataset.tab === 'checkin') loadCheckins();
            if (btn.dataset.tab === 'stats') loadStats();
        });
    });

    document.getElementById('playerForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = Object.fromEntries(new FormData(e.target));
        const r = await api('/api/players', 'POST', data);
        if (r.success) {
            e.target.reset();
            showToast('添加成功');
            loadPlayers();
        } else {
            showToast(r.error || '添加失败', true);
        }
    });

    document.getElementById('campForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = Object.fromEntries(new FormData(e.target));
        const r = await api('/api/camps', 'POST', data);
        if (r.success) {
            e.target.reset();
            showToast('添加成功');
            loadCamps();
        } else {
            showToast(r.error || '添加失败', true);
        }
    });

    document.getElementById('registerForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = Object.fromEntries(new FormData(e.target));
        const r = await api('/api/register', 'POST', data);
        showToast(r.message, !r.success);
        if (r.success) {
            e.target.reset();
            loadCamps();
            loadRegistrations();
            loadStats();
        }
    });

    document.getElementById('checkinForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = Object.fromEntries(new FormData(e.target));
        const r = await api('/api/checkin', 'POST', data);
        showToast(r.message, !r.success);
        if (r.success) {
            e.target.reset();
            loadCheckins();
            loadPlayers();
        }
    });

    document.getElementById('playerCheckinForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = Object.fromEntries(new FormData(e.target));
        const r = await api(`/api/player/${data.player_id}/checkins/month`);
        const p = players.find(x => x.id == data.player_id);
        document.getElementById('playerCheckinResult').innerHTML = `
            <p class="stat-month">${r.month}</p>
            <p class="stat-result"><strong>${p ? p.nickname : ''}</strong> 本月签到 <span class="stat-number">${r.count}</span> 次</p>
        `;
    });

    document.getElementById('modalCancel').addEventListener('click', closeModal);
    document.getElementById('modal').addEventListener('click', (e) => {
        if (e.target.id === 'modal') closeModal();
    });
});

window.editPlayer = editPlayer;
window.deletePlayer = deletePlayer;
window.editCamp = editCamp;
window.deleteCamp = deleteCamp;
