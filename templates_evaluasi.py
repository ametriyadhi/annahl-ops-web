"""
Templates & Komponen Tampilan HTML/JS untuk Modul Evaluasi & Rapor Personil (OB & Gardener)
An Nahl Ops Web Dashboard - note-umum.ametriyadhi.com
"""

TAB_EVALUASI_HTML = """
<!-- TAB EVALUASI & RAPOR KINERJA PERSONIL (OB & GARDENER) -->
<div id="tab-evaluasi" class="tab-content hidden space-y-6">

    <!-- Header & Action Bar -->
    <div class="bg-white rounded-2xl shadow-xs border border-slate-200/80 p-4 sm:p-6 space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
            <div>
                <div class="flex items-center gap-2">
                    <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-indigo-100 text-indigo-800 tracking-wider uppercase">Supervisi & Evaluasi SDM</span>
                    <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-100 text-slate-600">Unit OB & Gardener</span>
                </div>
                <h2 class="text-base sm:text-xl font-bold text-slate-800 flex items-center gap-2 mt-1">
                    <i class="fa-solid fa-chart-user text-indigo-600"></i>
                    Rapor & Analisa Kedisiplinan Personil (OB & Gardener)
                </h2>
                <p class="text-xs text-slate-500 mt-0.5">Analisis kedisiplinan jam standby pos geotagging, kepatuhan radius lokasi (geofence), dan pemberian catatan evaluasi pimpinan.</p>
            </div>
            <div class="flex items-center gap-2 sm:gap-3 flex-wrap">
                <button type="button" onclick="loadEvaluasiData()" class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition flex items-center gap-1.5 cursor-pointer">
                    <i class="fa-solid fa-arrows-rotate"></i> Refresh
                </button>
                <a href="/export/evaluasi" target="_blank" class="px-3 py-1.5 bg-slate-700 hover:bg-slate-800 text-white text-xs font-semibold rounded-lg transition shadow-xs flex items-center gap-1.5">
                    <i class="fa-solid fa-file-csv"></i> Ekspor Rapor CSV
                </a>
            </div>
        </div>

        <!-- 4 Top KPI Metric Cards -->
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
            <div class="bg-gradient-to-br from-indigo-50 to-blue-50/60 border border-indigo-200/80 rounded-xl p-3 sm:p-4">
                <span class="text-[10px] sm:text-xs font-bold text-indigo-800 uppercase tracking-wider block">Total Personil Aktif</span>
                <div class="mt-1 flex items-baseline gap-2">
                    <span id="eval-stat-personnel" class="text-xl sm:text-2xl font-black text-indigo-900">0</span>
                    <span class="text-[10px] text-indigo-600 font-semibold">personil</span>
                </div>
                <span id="eval-stat-checkins" class="text-[10px] text-slate-500 mt-1 block">0 total rekaman check-in</span>
            </div>

            <div class="bg-gradient-to-br from-teal-50 to-emerald-50/60 border border-teal-200/80 rounded-xl p-3 sm:p-4">
                <span class="text-[10px] sm:text-xs font-bold text-teal-800 uppercase tracking-wider block">Tingkat Tepat Waktu</span>
                <div class="mt-1 flex items-baseline gap-2">
                    <span id="eval-stat-compliance" class="text-xl sm:text-2xl font-black text-teal-700">0%</span>
                    <span class="text-[10px] text-teal-600 font-semibold">disiplin pos</span>
                </div>
                <div class="w-full bg-teal-200/50 rounded-full h-1.5 mt-2 overflow-hidden">
                    <div id="eval-stat-compliance-bar" class="bg-teal-600 h-1.5 rounded-full transition-all duration-500" style="width: 0%"></div>
                </div>
            </div>

            <div class="bg-gradient-to-br from-amber-50 to-orange-50/60 border border-amber-200/80 rounded-xl p-3 sm:p-4">
                <span class="text-[10px] sm:text-xs font-bold text-amber-800 uppercase tracking-wider block">Total Keterlambatan</span>
                <div class="mt-1 flex items-baseline gap-2">
                    <span id="eval-stat-late" class="text-xl sm:text-2xl font-black text-amber-700">0</span>
                    <span class="text-[10px] text-amber-600 font-semibold">kejadian</span>
                </div>
                <span id="eval-stat-late-pct" class="text-[10px] text-amber-700 mt-1 block">0% dari seluruh sesi</span>
            </div>

            <div class="bg-gradient-to-br from-rose-50 to-red-50/60 border border-rose-200/80 rounded-xl p-3 sm:p-4">
                <span class="text-[10px] sm:text-xs font-bold text-rose-800 uppercase tracking-wider block">Anomali Luar Radius</span>
                <div class="mt-1 flex items-baseline gap-2">
                    <span id="eval-stat-radius" class="text-xl sm:text-2xl font-black text-rose-700">0</span>
                    <span class="text-[10px] text-rose-600 font-semibold">kejadian</span>
                </div>
                <span id="eval-stat-radius-pct" class="text-[10px] text-rose-600 mt-1 block">>50m dari titik pos fisik</span>
            </div>
        </div>

        <!-- Filter Bar -->
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-t border-slate-100 pt-3">
            <div class="flex items-center gap-2 flex-wrap">
                <!-- Filter Unit -->
                <div class="flex items-center bg-slate-100 p-0.5 rounded-lg border border-slate-200/60 text-xs">
                    <button type="button" onclick="setEvaluasiUnitFilter('ALL')" id="eval-btn-unit-all" class="px-2.5 py-1 rounded-md font-semibold text-slate-700 bg-white shadow-xs transition cursor-pointer">Semua Unit</button>
                    <button type="button" onclick="setEvaluasiUnitFilter('OB')" id="eval-btn-unit-ob" class="px-2.5 py-1 rounded-md font-semibold text-slate-500 hover:text-slate-700 transition cursor-pointer">🧹 Office Boy</button>
                    <button type="button" onclick="setEvaluasiUnitFilter('GARDENER')" id="eval-btn-unit-gardener" class="px-2.5 py-1 rounded-md font-semibold text-slate-500 hover:text-slate-700 transition cursor-pointer">🌿 Gardener</button>
                </div>

                <!-- Filter Kategori Kinerja -->
                <select id="eval-filter-category" onchange="renderEvaluasiTable()" class="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 font-semibold text-slate-700 focus:outline-none focus:ring-1 focus:ring-indigo-500">
                    <option value="ALL">Semua Kategori Rapor</option>
                    <option value="TELADAN">🌟 Sangat Disiplin (Skor ≥ 85)</option>
                    <option value="BAIK">🟢 Baik & Produktif (Skor 70-84)</option>
                    <option value="CUKUP">🟡 Cukup / Perlu Arahan (Skor 50-69)</option>
                    <option value="PEMBINAAN">🔴 Butuh Pembinaan Khusus</option>
                </select>
            </div>

            <div class="text-xs text-slate-500 font-medium">
                💡 <span class="font-bold text-slate-700">Tips Pimpinan:</span> Klik nama petugas untuk melihat riwayat jam keterlambatan dan menulis catatan pembinaan.
            </div>
        </div>
    </div>

    <!-- 2 WIDGET PRIORITAS SUPERVISI (TOP TELAT & TOP LUAR RADIUS) -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <!-- Widget 1: Top Personil Paling Sering Terlambat -->
        <div class="bg-white rounded-2xl shadow-xs border border-amber-200/70 p-4 sm:p-5 space-y-3">
            <div class="flex items-center justify-between border-b border-amber-100 pb-3">
                <div class="flex items-center gap-2">
                    <div class="w-7 h-7 rounded-lg bg-amber-100 text-amber-700 flex items-center justify-center font-bold text-xs">
                        <i class="fa-solid fa-clock-rotate-left"></i>
                    </div>
                    <div>
                        <h3 class="text-xs sm:text-sm font-bold text-slate-800">Personil Paling Sering Terlambat</h3>
                        <p class="text-[11px] text-slate-500">Prioritas perhatian jam standby pagi/siang</p>
                    </div>
                </div>
                <span class="text-[10px] font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">Perhatian Supervisi</span>
            </div>
            <div id="eval-top-late-container" class="space-y-2.5">
                <!-- Dynamic injected top late list -->
                <p class="text-xs text-slate-400 py-4 text-center">Memuat daftar keterlambatan...</p>
            </div>
        </div>

        <!-- Widget 2: Top Checkin di Luar Radius Pos -->
        <div class="bg-white rounded-2xl shadow-xs border border-rose-200/70 p-4 sm:p-5 space-y-3">
            <div class="flex items-center justify-between border-b border-rose-100 pb-3">
                <div class="flex items-center gap-2">
                    <div class="w-7 h-7 rounded-lg bg-rose-100 text-rose-700 flex items-center justify-center font-bold text-xs">
                        <i class="fa-solid fa-location-crosshairs"></i>
                    </div>
                    <div>
                        <h3 class="text-xs sm:text-sm font-bold text-slate-800">Personil Sering Check-in di Luar Pos</h3>
                        <p class="text-[11px] text-slate-500">Terdeteksi >35–50 meter dari titik fisik pos</p>
                    </div>
                </div>
                <span class="text-[10px] font-bold text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full border border-rose-200">Audit Lokasi</span>
            </div>
            <div id="eval-top-radius-container" class="space-y-2.5">
                <!-- Dynamic injected top out-radius list -->
                <p class="text-xs text-slate-400 py-4 text-center">Memuat data lokasi geofence...</p>
            </div>
        </div>
    </div>

    <!-- TABEL LEADERBOARD RAPOR KINERJA SELURUH PERSONIL -->
    <div class="bg-white rounded-2xl shadow-xs border border-slate-200/80 overflow-hidden">
        <div class="p-4 bg-slate-50/80 border-b border-slate-200/80 flex items-center justify-between flex-wrap gap-2">
            <div>
                <h3 class="text-sm font-bold text-slate-800 flex items-center gap-2">
                    <i class="fa-solid fa-award text-amber-500"></i>
                    Matriks Rapor & Peringkat Kedisiplinan Personil
                </h3>
                <p class="text-xs text-slate-500">Dihitung otomatis berdasarkan ketepatan waktu checkin, kepatuhan radius GPS, dan keaktifan tugas.</p>
            </div>
            <span id="eval-table-count" class="text-xs font-semibold text-slate-500">Menampilkan 0 personil</span>
        </div>

        <div class="overflow-x-auto">
            <table class="w-full text-left text-xs border-collapse">
                <thead>
                    <tr class="bg-slate-100 text-slate-700 font-bold border-b border-slate-200 uppercase tracking-wider text-[10px]">
                        <th class="py-3 px-3 w-10 text-center">Rank</th>
                        <th class="py-3 px-3 min-w-[150px]">Nama Personil</th>
                        <th class="py-3 px-2 w-24 text-center">Unit</th>
                        <th class="py-3 px-2 w-20 text-center">Total Pos</th>
                        <th class="py-3 px-3 text-center">Tepat Waktu</th>
                        <th class="py-3 px-3 text-center">Terlambat</th>
                        <th class="py-3 px-3 text-center">Luar Radius</th>
                        <th class="py-3 px-3 text-center min-w-[110px]">Rata-rata Telat</th>
                        <th class="py-3 px-3 text-center w-28">Skor Disiplin</th>
                        <th class="py-3 px-3 text-center w-36">Status Rapor</th>
                        <th class="py-3 px-3 min-w-[180px]">Catatan Supervisi Mr Slam</th>
                        <th class="py-3 px-3 w-20 text-center">Aksi</th>
                    </tr>
                </thead>
                <tbody id="eval-table-tbody" class="divide-y divide-slate-100 text-slate-700">
                    <tr><td colspan="12" class="text-center py-8 text-slate-400">Memuat data rapor personil...</td></tr>
                </tbody>
            </table>
        </div>
    </div>
</div>

<!-- MODAL DETAIL PROFIL & BERI CATATAN SUPERVISI -->
<div id="modal-evaluasi-petugas" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs hidden">
    <div class="bg-white rounded-2xl shadow-xl border border-slate-200 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div class="p-5 border-b border-slate-100 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div id="eval-modal-avatar" class="w-10 h-10 rounded-xl bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-base">
                    👤
                </div>
                <div>
                    <h3 id="eval-modal-name" class="font-bold text-slate-800 text-base">Nama Petugas</h3>
                    <p id="eval-modal-unit-badge" class="text-xs text-slate-500">Unit: OB</p>
                </div>
            </div>
            <button type="button" onclick="closeModalEvaluasi()" class="text-slate-400 hover:text-slate-600 text-lg cursor-pointer">
                <i class="fa-solid fa-xmark"></i>
            </button>
        </div>

        <div class="p-5 space-y-5 text-xs">
            <!-- 3 Mini Stats -->
            <div class="grid grid-cols-3 gap-3">
                <div class="bg-slate-50 border border-slate-200 rounded-xl p-3 text-center">
                    <span class="text-[10px] text-slate-400 uppercase font-bold block">Skor Disiplin</span>
                    <span id="eval-modal-score" class="text-xl font-black text-slate-800 mt-0.5 block">0</span>
                    <span id="eval-modal-badge" class="text-[10px] font-semibold text-emerald-600">-</span>
                </div>
                <div class="bg-amber-50/60 border border-amber-200 rounded-xl p-3 text-center">
                    <span class="text-[10px] text-amber-700 uppercase font-bold block">Total Terlambat</span>
                    <span id="eval-modal-late" class="text-xl font-black text-amber-800 mt-0.5 block">0x</span>
                    <span id="eval-modal-late-info" class="text-[10px] text-amber-600">Avg: 0 mnt</span>
                </div>
                <div class="bg-rose-50/60 border border-rose-200 rounded-xl p-3 text-center">
                    <span class="text-[10px] text-rose-700 uppercase font-bold block">Luar Radius</span>
                    <span id="eval-modal-radius" class="text-xl font-black text-rose-800 mt-0.5 block">0x</span>
                    <span id="eval-modal-radius-info" class="text-[10px] text-rose-600">Max: 0 m</span>
                </div>
            </div>

            <!-- Rekomendasi Sistem -->
            <div class="bg-indigo-50/60 border border-indigo-100 p-3 rounded-xl flex items-start gap-2.5">
                <i class="fa-solid fa-lightbulb text-indigo-600 mt-0.5 text-sm"></i>
                <div>
                    <span class="font-bold text-indigo-900 block text-xs">Analisa Otomatis Sistem:</span>
                    <p id="eval-modal-rec" class="text-slate-600 text-[11px] mt-0.5">-</p>
                </div>
            </div>

            <!-- Riwayat Kasus Terlambat Terakhir -->
            <div class="space-y-2">
                <h4 class="font-bold text-slate-800 flex items-center gap-1.5">
                    <i class="fa-solid fa-clock-rotate-left text-amber-600"></i> Riwayat 5 Keterlambatan Terakhir:
                </h4>
                <div id="eval-modal-late-list" class="space-y-1.5">
                    <!-- Dynamic -->
                </div>
            </div>

            <!-- Form Catatan Supervisi Pimpinan (Mr Slam) -->
            <form id="form-evaluasi-notes" onsubmit="submitSupervisorNotes(event)" class="space-y-3 border-t border-slate-100 pt-4">
                <input type="hidden" id="eval-form-petugas" name="petugas_name" value="">
                <input type="hidden" id="eval-form-unit" name="unit_code" value="">

                <div>
                    <label class="block font-bold text-slate-800 mb-1">
                        <i class="fa-solid fa-pen-to-square text-indigo-600"></i> Catatan Evaluasi & Coaching dari Mr Slam:
                    </label>
                    <textarea id="eval-form-notes" name="notes" rows="3" placeholder="Tuliskan arahan, tindak lanjut evaluasi, atau catatan apresiasi untuk petugas ini..." class="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"></textarea>
                    <span class="text-[10px] text-slate-400 mt-1 block">Catatan ini akan tersimpan permanen dan muncul pada tabel rekap evaluasi bulanan.</span>
                </div>

                <div class="flex items-center justify-end gap-2">
                    <button type="button" onclick="closeModalEvaluasi()" class="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-lg transition cursor-pointer">Tutup</button>
                    <button type="submit" id="eval-btn-save-notes" class="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg transition shadow-xs cursor-pointer flex items-center gap-1.5">
                        <i class="fa-solid fa-floppy-disk"></i> Simpan Catatan Evaluasi
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>
"""

EVALUASI_CLIENT_SCRIPT = """
<script>
// --- CLIENT CONTROLLER EVALUASI & RAPOR KINERJA PERSONIL (OB & GARDENER) ---

let evaluasiDataCache = null;
let currentEvaluasiUnit = 'ALL';

async function loadEvaluasiData() {
    try {
        const res = await fetch(`/api/ops/evaluasi/summary?unit=${currentEvaluasiUnit}`);
        const data = await res.json();
        evaluasiDataCache = data;

        // 1. KPI Cards
        document.getElementById('eval-stat-personnel').innerText = data.total_personnel || 0;
        document.getElementById('eval-stat-checkins').innerText = `${data.total_checkins || 0} total rekaman check-in`;
        document.getElementById('eval-stat-compliance').innerText = `${data.compliance_rate || 0}%`;
        document.getElementById('eval-stat-compliance-bar').style.width = `${data.compliance_rate || 0}%`;
        document.getElementById('eval-stat-late').innerText = data.top_late?.reduce((a, b) => a + b.terlambat, 0) || 0;
        document.getElementById('eval-stat-late-pct').innerText = `${data.late_rate || 0}% dari seluruh sesi check-in`;
        document.getElementById('eval-stat-radius').innerText = data.top_out_radius?.reduce((a, b) => a + b.diluar_radius, 0) || 0;
        document.getElementById('eval-stat-radius-pct').innerText = `${data.out_radius_rate || 0}% dari seluruh sesi check-in`;

        // 2. Render Widgets & Table
        renderEvaluasiWidgets(data.top_late || [], data.top_out_radius || []);
        renderEvaluasiTable();

    } catch (err) {
        console.error('Error loadEvaluasiData:', err);
    }
}

function setEvaluasiUnitFilter(unit) {
    currentEvaluasiUnit = unit;
    const btnAll = document.getElementById('eval-btn-unit-all');
    const btnOb = document.getElementById('eval-btn-unit-ob');
    const btnGardener = document.getElementById('eval-btn-unit-gardener');

    [btnAll, btnOb, btnGardener].forEach(b => {
        b.className = "px-2.5 py-1 rounded-md font-semibold text-slate-500 hover:text-slate-700 transition cursor-pointer";
    });

    if (unit === 'ALL') {
        btnAll.className = "px-2.5 py-1 rounded-md font-semibold text-slate-700 bg-white shadow-xs transition cursor-pointer";
    } else if (unit === 'OB') {
        btnOb.className = "px-2.5 py-1 rounded-md font-semibold text-slate-700 bg-white shadow-xs transition cursor-pointer";
    } else if (unit === 'GARDENER') {
        btnGardener.className = "px-2.5 py-1 rounded-md font-semibold text-slate-700 bg-white shadow-xs transition cursor-pointer";
    }

    loadEvaluasiData();
}

function renderEvaluasiWidgets(topLate, topRadius) {
    // 1. Top Late Widget
    const lateContainer = document.getElementById('eval-top-late-container');
    if (lateContainer) {
        if (!topLate.length) {
            lateContainer.innerHTML = '<p class="text-xs text-slate-400 py-3 text-center">Tidak ada catatan keterlambatan pada periode ini. Luar biasa! 👏</p>';
        } else {
            lateContainer.innerHTML = topLate.slice(0, 5).map((p, idx) => {
                const barWidth = Math.min(100, p.late_pct);
                return `
                    <div class="p-2.5 bg-slate-50 hover:bg-amber-50/50 rounded-xl border border-slate-100 transition space-y-1.5">
                        <div class="flex items-center justify-between text-xs">
                            <div class="flex items-center gap-2">
                                <span class="w-5 h-5 rounded-full bg-amber-100 text-amber-800 flex items-center justify-center font-bold text-[10px]">${idx + 1}</span>
                                <span class="font-bold text-slate-800">${escapeHtml(p.nama)}</span>
                                <span class="text-[10px] text-slate-400 font-semibold">(${p.unit})</span>
                            </div>
                            <div class="text-right">
                                <span class="font-bold text-amber-700 text-xs">${p.terlambat}x Telat</span>
                                <span class="text-[10px] text-slate-400"> (${p.late_pct}%)</span>
                            </div>
                        </div>
                        <div class="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
                            <div class="bg-amber-500 h-1.5 rounded-full" style="width: ${barWidth}%"></div>
                        </div>
                        <div class="flex items-center justify-between text-[10px] text-slate-500 pt-0.5">
                            <span>Rata-rata telat: <strong class="text-slate-700">${p.avg_late_min} mnt</strong></span>
                            <span>Paling telat: <strong class="text-rose-600">${p.max_late_min} mnt</strong></span>
                            <button type="button" onclick="openModalEvaluasi('${escapeHtml(p.nama)}')" class="text-indigo-600 hover:text-indigo-800 font-bold cursor-pointer">Beri Arahan →</button>
                        </div>
                    </div>
                `;
            }).join('');
        }
    }

    // 2. Top Out-Radius Widget
    const radiusContainer = document.getElementById('eval-top-radius-container');
    if (radiusContainer) {
        if (!topRadius.length) {
            radiusContainer.innerHTML = '<p class="text-xs text-slate-400 py-3 text-center">Seluruh checkin berada di dalam radius pos. Sangat tertib! 🎯</p>';
        } else {
            radiusContainer.innerHTML = topRadius.slice(0, 5).map((p, idx) => {
                const barWidth = Math.min(100, p.out_radius_pct);
                return `
                    <div class="p-2.5 bg-slate-50 hover:bg-rose-50/50 rounded-xl border border-slate-100 transition space-y-1.5">
                        <div class="flex items-center justify-between text-xs">
                            <div class="flex items-center gap-2">
                                <span class="w-5 h-5 rounded-full bg-rose-100 text-rose-800 flex items-center justify-center font-bold text-[10px]">${idx + 1}</span>
                                <span class="font-bold text-slate-800">${escapeHtml(p.nama)}</span>
                                <span class="text-[10px] text-slate-400 font-semibold">(${p.unit})</span>
                            </div>
                            <div class="text-right">
                                <span class="font-bold text-rose-700 text-xs">${p.diluar_radius}x Luar Pos</span>
                                <span class="text-[10px] text-slate-400"> (${p.out_radius_pct}%)</span>
                            </div>
                        </div>
                        <div class="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
                            <div class="bg-rose-500 h-1.5 rounded-full" style="width: ${barWidth}%"></div>
                        </div>
                        <div class="flex items-center justify-between text-[10px] text-slate-500 pt-0.5">
                            <span>Jarak rata-rata: <strong class="text-slate-700">${p.avg_dist} m</strong></span>
                            <span>Jarak terjauh: <strong class="text-rose-600">${p.max_dist} m</strong></span>
                            <button type="button" onclick="openModalEvaluasi('${escapeHtml(p.nama)}')" class="text-indigo-600 hover:text-indigo-800 font-bold cursor-pointer">Periksa →</button>
                        </div>
                    </div>
                `;
            }).join('');
        }
    }
}

function renderEvaluasiTable() {
    if (!evaluasiDataCache || !evaluasiDataCache.leaderboard) return;

    const catFilter = document.getElementById('eval-filter-category').value;
    const tbody = document.getElementById('eval-table-tbody');
    const countBadge = document.getElementById('eval-table-count');

    let items = evaluasiDataCache.leaderboard;
    if (catFilter !== 'ALL') {
        items = items.filter(p => p.eval_category === catFilter);
    }

    if (countBadge) {
        countBadge.innerText = `Menampilkan ${items.length} personil`;
    }

    if (!items.length) {
        tbody.innerHTML = '<tr><td colspan="12" class="text-center py-8 text-slate-400">Tidak ada personil yang sesuai dengan filter.</td></tr>';
        return;
    }

    tbody.innerHTML = items.map((p, idx) => {
        let badgeStyle = "bg-emerald-100 text-emerald-800";
        if (p.eval_category === 'BAIK') badgeStyle = "bg-teal-100 text-teal-800";
        else if (p.eval_category === 'CUKUP') badgeStyle = "bg-amber-100 text-amber-800";
        else if (p.eval_category === 'PEMBINAAN') badgeStyle = "bg-rose-100 text-rose-800";

        let scoreColor = "text-emerald-700";
        if (p.discipline_score < 70) scoreColor = "text-amber-700";
        if (p.discipline_score < 50) scoreColor = "text-rose-700";

        let unitBadge = p.unit === 'GARDENER' 
            ? '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">🌿 Gardener</span>'
            : '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-sky-100 text-sky-800">🧹 OB</span>';

        let notesDisplay = p.supervisor_notes 
            ? `<span class="text-slate-800 font-medium block">"${escapeHtml(p.supervisor_notes)}"</span>`
            : `<span class="text-slate-400 italic">Belum ada catatan</span>`;

        return `
            <tr class="hover:bg-slate-50/80 transition">
                <td class="py-2.5 px-3 text-center font-bold ${idx < 3 ? 'text-amber-500' : 'text-slate-400'}">${idx + 1}</td>
                <td class="py-2.5 px-3">
                    <span class="font-bold text-slate-800 block cursor-pointer hover:text-indigo-600 transition" onclick="openModalEvaluasi('${escapeHtml(p.nama)}')">${escapeHtml(p.nama)}</span>
                    <span class="text-[10px] text-slate-400">${p.days_active} hari kerja aktif</span>
                </td>
                <td class="py-2.5 px-2 text-center">${unitBadge}</td>
                <td class="py-2.5 px-2 text-center font-semibold text-slate-700">${p.total_checkin}x</td>
                <td class="py-2.5 px-3 text-center">
                    <span class="font-bold text-teal-700 block">${p.tepat_waktu}x</span>
                    <span class="text-[10px] text-teal-600">(${p.on_time_pct}%)</span>
                </td>
                <td class="py-2.5 px-3 text-center">
                    <span class="font-bold ${p.terlambat > 0 ? 'text-amber-700' : 'text-slate-400'} block">${p.terlambat}x</span>
                    <span class="text-[10px] text-amber-600">(${p.late_pct}%)</span>
                </td>
                <td class="py-2.5 px-3 text-center">
                    <span class="font-bold ${p.diluar_radius > 0 ? 'text-rose-700' : 'text-slate-400'} block">${p.diluar_radius}x</span>
                    <span class="text-[10px] text-rose-600">(${p.out_radius_pct}%)</span>
                </td>
                <td class="py-2.5 px-3 text-center">
                    <span class="font-semibold text-slate-700 block">${p.avg_late_min} mnt</span>
                    <span class="text-[10px] text-slate-400">max: ${p.max_late_min}m</span>
                </td>
                <td class="py-2.5 px-3 text-center">
                    <span class="text-sm font-black ${scoreColor} block">${p.discipline_score}</span>
                    <div class="w-16 bg-slate-200 rounded-full h-1 mx-auto mt-1 overflow-hidden">
                        <div class="bg-indigo-600 h-1 rounded-full" style="width: ${p.discipline_score}%"></div>
                    </div>
                </td>
                <td class="py-2.5 px-3 text-center">
                    <span class="px-2.5 py-1 rounded-full text-[10px] font-bold ${badgeStyle} inline-block whitespace-nowrap">${p.eval_badge}</span>
                </td>
                <td class="py-2.5 px-3 max-w-xs">
                    ${notesDisplay}
                </td>
                <td class="py-2.5 px-3 text-center">
                    <button type="button" onclick="openModalEvaluasi('${escapeHtml(p.nama)}')" class="px-2.5 py-1 bg-indigo-50 hover:bg-indigo-600 text-indigo-700 hover:text-white rounded text-[10px] font-bold transition shadow-2xs cursor-pointer">
                        Rapor
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

function openModalEvaluasi(petugasName) {
    if (!evaluasiDataCache || !evaluasiDataCache.leaderboard) return;

    const p = evaluasiDataCache.leaderboard.find(x => x.nama === petugasName);
    if (!p) return;

    const modal = document.getElementById('modal-evaluasi-petugas');
    document.getElementById('eval-modal-name').innerText = p.nama;
    document.getElementById('eval-modal-unit-badge').innerText = `Unit: ${p.unit} • Total Check-in: ${p.total_checkin} kali (${p.days_active} hari aktif)`;
    document.getElementById('eval-modal-score').innerText = p.discipline_score;
    document.getElementById('eval-modal-badge').innerText = p.eval_badge;
    document.getElementById('eval-modal-late').innerText = `${p.terlambat}x (${p.late_pct}%)`;
    document.getElementById('eval-modal-late-info').innerText = `Avg: ${p.avg_late_min}m | Max: ${p.max_late_min}m`;
    document.getElementById('eval-modal-radius').innerText = `${p.diluar_radius}x (${p.out_radius_pct}%)`;
    document.getElementById('eval-modal-radius-info').innerText = `Avg: ${p.avg_dist}m | Max: ${p.max_dist}m`;
    document.getElementById('eval-modal-rec').innerText = p.recommendation;

    // Render late list
    const lateList = document.getElementById('eval-modal-late-list');
    if (!p.late_details || !p.late_details.length) {
        lateList.innerHTML = '<p class="text-slate-400 italic">Tidak ada catatan keterlambatan terbaru.</p>';
    } else {
        lateList.innerHTML = p.late_details.map(d => `
            <div class="flex items-center justify-between p-2 bg-amber-50/60 border border-amber-100 rounded-lg text-[11px]">
                <div>
                    <span class="font-bold text-slate-800">${d.date} (${d.session})</span>
                    <span class="text-slate-500 block">${escapeHtml(d.pos)} • Pukul ${d.time}</span>
                </div>
                <span class="font-bold text-rose-600 bg-white px-2 py-0.5 rounded border border-rose-200">Telat ${d.minutes_late} Menit</span>
            </div>
        `).join('');
    }

    // Prefill form
    document.getElementById('eval-form-petugas').value = p.nama;
    document.getElementById('eval-form-unit').value = p.unit;
    document.getElementById('eval-form-notes').value = p.supervisor_notes || '';

    modal.classList.remove('hidden');
}

function closeModalEvaluasi() {
    const modal = document.getElementById('modal-evaluasi-petugas');
    if (modal) modal.classList.add('hidden');
}

async function submitSupervisorNotes(event) {
    event.preventDefault();
    const btn = document.getElementById('eval-btn-save-notes');
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Menyimpan...';

    const form = document.getElementById('form-evaluasi-notes');
    const formData = new FormData(form);

    const payload = {
        petugas_name: formData.get('petugas_name'),
        unit_code: formData.get('unit_code'),
        notes: formData.get('notes')
    };

    try {
        const res = await fetch('/api/ops/evaluasi/notes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await res.json();
        if (result.success) {
            alert('✓ Catatan evaluasi supervisi berhasil disimpan!');
            closeModalEvaluasi();
            loadEvaluasiData();
        } else {
            alert('Gagal: ' + (result.error || 'Terjadi kesalahan'));
        }
    } catch (e) {
        alert('Error koneksi: ' + e.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> Simpan Catatan Evaluasi';
    }
}
</script>
"""
