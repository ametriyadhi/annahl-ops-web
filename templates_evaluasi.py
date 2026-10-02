"""
Templates & Komponen Tampilan HTML/JS untuk Modul Evaluasi & Rapor Personil (OB & Gardener)
An Nahl Ops Web Dashboard - note-umum.ametriyadhi.com
Standardisasi Target Sesi Pos yang Adil, Filter Per Tanggal Fleksibel, Analisis Mangkir Pos & Rekap Disiplin
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
                    <span id="eval-header-period-badge" class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-teal-100 text-teal-800 uppercase tracking-wider">Periode: Memuat...</span>
                </div>
                <h2 class="text-base sm:text-xl font-bold text-slate-800 flex items-center gap-2 mt-1">
                    <i class="fa-solid fa-clipboard-user text-indigo-600"></i>
                    Rapor & Evaluasi Kedisiplinan Personil (OB & Gardener)
                </h2>
                <p class="text-xs text-slate-500 mt-0.5">Penilaian kinerja adil berbasis kewajiban sesi standby unit. Deteksi mangkir pos (alpha/tidak checkin), keterlambatan jam tiba, dan radius geofence.</p>
            </div>
            <div class="flex items-center gap-2 sm:gap-3 flex-wrap">
                <button type="button" onclick="loadEvaluasiData()" class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition flex items-center gap-1.5 cursor-pointer">
                    <i class="fa-solid fa-arrows-rotate"></i> Refresh
                </button>
                <a id="eval-btn-export-csv" href="/export/evaluasi" target="_blank" class="px-3 py-1.5 bg-slate-700 hover:bg-slate-800 text-white text-xs font-semibold rounded-lg transition shadow-xs flex items-center gap-1.5">
                    <i class="fa-solid fa-file-csv"></i> Ekspor Rapor CSV
                </a>
            </div>
        </div>

        <!-- PANEL FILTER RENTANG WAKTU (MURNI PER TANGGAL) -->
        <div class="bg-slate-50/90 border border-slate-200/90 rounded-xl p-3.5 space-y-3">
            <div class="flex flex-col md:flex-row md:items-center justify-between gap-3">
                
                <!-- Date Inputs & Action Buttons -->
                <div class="flex items-center gap-2.5 flex-wrap">
                    <span class="text-xs font-bold text-slate-700 flex items-center gap-1.5 mr-1">
                        <i class="fa-regular fa-calendar-days text-indigo-600 text-sm"></i> Filter Tanggal Evaluasi:
                    </span>
                    <div class="flex items-center gap-1.5 text-xs">
                        <label for="eval-start-date" class="text-slate-500 font-medium">Dari:</label>
                        <input type="date" id="eval-start-date" onchange="applyCustomDateRange()" class="bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 font-semibold text-slate-700 text-xs focus:ring-2 focus:ring-indigo-500 focus:outline-none shadow-2xs">
                    </div>
                    <div class="flex items-center gap-1.5 text-xs">
                        <label for="eval-end-date" class="text-slate-500 font-medium">Sampai:</label>
                        <input type="date" id="eval-end-date" onchange="applyCustomDateRange()" class="bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 font-semibold text-slate-700 text-xs focus:ring-2 focus:ring-indigo-500 focus:outline-none shadow-2xs">
                    </div>
                    <button type="button" onclick="applyCustomDateRange()" class="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-lg transition shadow-xs cursor-pointer flex items-center gap-1.5">
                        <i class="fa-solid fa-filter"></i> Terapkan
                    </button>
                    <button type="button" onclick="resetEvaluasiDateRange()" class="px-2.5 py-1.5 bg-slate-200 hover:bg-slate-300 text-slate-700 font-semibold text-xs rounded-lg transition cursor-pointer flex items-center gap-1" title="Tampilkan Seluruh Periode">
                        <i class="fa-solid fa-rotate-left"></i> Reset
                    </button>
                </div>

                <!-- Info Kewajiban Sesi Unit -->
                <div class="flex items-center gap-2 flex-wrap text-xs">
                    <span class="font-bold text-slate-700">🎯 Kewajiban Sesi:</span>
                    <span class="bg-sky-100 text-sky-800 px-2.5 py-1 rounded-lg font-semibold text-xs border border-sky-200/60">🧹 Unit OB: <strong id="eval-target-ob-badge">0</strong> Sesi</span>
                    <span class="bg-emerald-100 text-emerald-800 px-2.5 py-1 rounded-lg font-semibold text-xs border border-emerald-200/60">🌿 Unit Gardener: <strong id="eval-target-gardener-badge">0</strong> Sesi</span>
                </div>
            </div>
            
            <p class="text-[11px] text-slate-400 border-t border-slate-200/60 pt-2 italic">
                *Target kewajiban sesi dan rekap kehadiran dihitung dinamis sesuai masa berlaku jadwal masing-masing unit pada rentang tanggal yang dipilih.
            </p>
        </div>

        <!-- 4 Top KPI Metric Cards -->
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
            <!-- Card 1: Personil & Target Sesi -->
            <div class="bg-gradient-to-br from-indigo-50 to-blue-50/60 border border-indigo-200/80 rounded-xl p-3 sm:p-4">
                <span class="text-[10px] sm:text-xs font-bold text-indigo-800 uppercase tracking-wider block">Total Personil Terdata</span>
                <div class="mt-1 flex items-baseline gap-2">
                    <span id="eval-stat-personnel" class="text-xl sm:text-2xl font-black text-indigo-900">0</span>
                    <span class="text-[10px] text-indigo-600 font-semibold">personil</span>
                </div>
                <span id="eval-stat-sessions-info" class="text-[10px] text-slate-500 mt-1 block">Wajib: OB 0 • Gardener 0</span>
            </div>

            <!-- Card 2: Kehadiran Pos Global -->
            <div class="bg-gradient-to-br from-teal-50 to-emerald-50/60 border border-teal-200/80 rounded-xl p-3 sm:p-4">
                <span class="text-[10px] sm:text-xs font-bold text-teal-800 uppercase tracking-wider block">Tingkat Kehadiran Pos</span>
                <div class="mt-1 flex items-baseline gap-2">
                    <span id="eval-stat-attendance-rate" class="text-xl sm:text-2xl font-black text-teal-700">0%</span>
                    <span id="eval-stat-checkins" class="text-[10px] text-teal-600 font-semibold">0 check-in</span>
                </div>
                <div class="w-full bg-teal-200/50 rounded-full h-1.5 mt-2 overflow-hidden">
                    <div id="eval-stat-attendance-bar" class="bg-teal-600 h-1.5 rounded-full transition-all duration-500" style="width: 0%"></div>
                </div>
            </div>

            <!-- Card 3: Sesi Mangkir Pos (Alpha / Tidak Checkin) -->
            <div class="bg-gradient-to-br from-rose-50 to-red-50/60 border border-rose-200/80 rounded-xl p-3 sm:p-4">
                <span class="text-[10px] sm:text-xs font-bold text-rose-800 uppercase tracking-wider block">Mangkir Pos (Tidak Check-in)</span>
                <div class="mt-1 flex items-baseline gap-2">
                    <span id="eval-stat-missed" class="text-xl sm:text-2xl font-black text-rose-700">0</span>
                    <span class="text-[10px] text-rose-600 font-semibold">sesi kosong</span>
                </div>
                <span class="text-[10px] text-rose-600 mt-1 block">Posisi pos kosong tanpa laporan</span>
            </div>

            <!-- Card 4: Keterlambatan Jam Masuk -->
            <div class="bg-gradient-to-br from-amber-50 to-orange-50/60 border border-amber-200/80 rounded-xl p-3 sm:p-4">
                <span class="text-[10px] sm:text-xs font-bold text-amber-800 uppercase tracking-wider block">Total Keterlambatan</span>
                <div class="mt-1 flex items-baseline gap-2">
                    <span id="eval-stat-late" class="text-xl sm:text-2xl font-black text-amber-700">0</span>
                    <span class="text-[10px] text-amber-600 font-semibold">kali telat</span>
                </div>
                <span id="eval-stat-late-pct" class="text-[10px] text-amber-700 mt-1 block">0% dari sesi hadir</span>
            </div>
        </div>

        <!-- Filter Bar Unit & Status -->
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
                    <option value="TELADAN">🌟 Sangat Disiplin (Skor ≥ 80)</option>
                    <option value="BAIK">🟢 Baik & Produktif (Skor 65-79)</option>
                    <option value="CUKUP">🟡 Cukup / Perlu Arahan (Skor 50-64)</option>
                    <option value="PEMBINAAN">🔴 Butuh Pembinaan Khusus</option>
                </select>
            </div>

            <div class="text-xs text-slate-500 font-medium">
                💡 <span class="font-bold text-slate-700">Keadilan Penilaian:</span> Target sesi disesuaikan otomatis dengan masa aktif kerja masing-masing unit.
            </div>
        </div>
    </div>

    <!-- 3 WIDGET PRIORITAS SUPERVISI (TOP MANGKIR, TOP TELAT, TOP LUAR RADIUS) -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- Widget 1: Top Personil Mangkir Pos (Alpha) -->
        <div class="bg-white rounded-2xl shadow-xs border border-rose-200/80 p-4 space-y-3">
            <div class="flex items-center justify-between border-b border-rose-100 pb-2.5">
                <div class="flex items-center gap-2">
                    <div class="w-7 h-7 rounded-lg bg-rose-100 text-rose-700 flex items-center justify-center font-bold text-xs">
                        <i class="fa-solid fa-user-xmark"></i>
                    </div>
                    <div>
                        <h3 class="text-xs font-bold text-slate-800">Paling Sering Mangkir Pos</h3>
                        <p class="text-[10px] text-slate-500">Tidak melakukan check-in pos</p>
                    </div>
                </div>
                <span class="text-[9px] font-bold text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full border border-rose-200">Perhatian Utama</span>
            </div>
            <div id="eval-top-missed-container" class="space-y-2">
                <p class="text-xs text-slate-400 py-3 text-center">Memuat data mangkir...</p>
            </div>
        </div>

        <!-- Widget 2: Top Personil Terlambat -->
        <div class="bg-white rounded-2xl shadow-xs border border-amber-200/80 p-4 space-y-3">
            <div class="flex items-center justify-between border-b border-amber-100 pb-2.5">
                <div class="flex items-center gap-2">
                    <div class="w-7 h-7 rounded-lg bg-amber-100 text-amber-700 flex items-center justify-center font-bold text-xs">
                        <i class="fa-solid fa-clock-rotate-left"></i>
                    </div>
                    <div>
                        <h3 class="text-xs font-bold text-slate-800">Paling Sering Terlambat</h3>
                        <p class="text-[10px] text-slate-500">Hadir lewat dari jam toleransi</p>
                    </div>
                </div>
                <span class="text-[9px] font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">Jam Masuk</span>
            </div>
            <div id="eval-top-late-container" class="space-y-2">
                <p class="text-xs text-slate-400 py-3 text-center">Memuat keterlambatan...</p>
            </div>
        </div>

        <!-- Widget 3: Top Checkin Luar Radius -->
        <div class="bg-white rounded-2xl shadow-xs border border-purple-200/80 p-4 space-y-3">
            <div class="flex items-center justify-between border-b border-purple-100 pb-2.5">
                <div class="flex items-center gap-2">
                    <div class="w-7 h-7 rounded-lg bg-purple-100 text-purple-700 flex items-center justify-center font-bold text-xs">
                        <i class="fa-solid fa-location-crosshairs"></i>
                    </div>
                    <div>
                        <h3 class="text-xs font-bold text-slate-800">Check-in Luar Titik Pos</h3>
                        <p class="text-[10px] text-slate-500">Terdeteksi >35–50 meter dari pos</p>
                    </div>
                </div>
                <span class="text-[9px] font-bold text-purple-700 bg-purple-50 px-2 py-0.5 rounded-full border border-purple-200">Audit Lokasi</span>
            </div>
            <div id="eval-top-radius-container" class="space-y-2">
                <p class="text-xs text-slate-400 py-3 text-center">Memuat anomali lokasi...</p>
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
                <p class="text-xs text-slate-500">Target kewajiban sesi disesuaikan dengan masa berlaku jadwal masing-masing unit kerja pada rentang tanggal yang dipilih.</p>
            </div>
            <span id="eval-table-count" class="text-xs font-semibold text-slate-500">Menampilkan 0 personil</span>
        </div>

        <div class="overflow-x-auto">
            <table class="w-full text-left text-xs border-collapse">
                <thead>
                    <tr class="bg-slate-100 text-slate-700 font-bold border-b border-slate-200 uppercase tracking-wider text-[10px]">
                        <th class="py-3 px-3 w-10 text-center">Rank</th>
                        <th class="py-3 px-3 min-w-[140px]">Nama Personil</th>
                        <th class="py-3 px-2 w-20 text-center">Unit</th>
                        <th class="py-3 px-2 w-20 text-center bg-slate-200/60" title="Target kewajiban sesi operasional unit pada rentang tanggal yang dipilih">Wajib Sesi</th>
                        <th class="py-3 px-2 w-20 text-center text-teal-800" title="Jumlah checkin riil yang terlaksana">Hadir</th>
                        <th class="py-3 px-2 w-24 text-center bg-rose-50 text-rose-800" title="Jumlah sesi pos yang ditinggalkan tanpa checkin">Mangkir (Alpha)</th>
                        <th class="py-3 px-3 text-center" title="Persentase kehadiran terhadap kewajiban sesi unit">Kehadiran (%)</th>
                        <th class="py-3 px-3 text-center">Tepat Waktu</th>
                        <th class="py-3 px-3 text-center">Terlambat</th>
                        <th class="py-3 px-3 text-center">Luar Radius</th>
                        <th class="py-3 px-3 text-center w-28">Skor Disiplin</th>
                        <th class="py-3 px-3 text-center w-36">Status Rapor</th>
                        <th class="py-3 px-3 min-w-[170px]">Catatan Supervisi Mr Slam</th>
                        <th class="py-3 px-3 w-20 text-center">Aksi</th>
                    </tr>
                </thead>
                <tbody id="eval-table-tbody" class="divide-y divide-slate-100 text-slate-700">
                    <tr><td colspan="14" class="text-center py-8 text-slate-400">Memuat data rapor personil...</td></tr>
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
            <!-- 4 Mini Stats -->
            <div class="grid grid-cols-4 gap-2.5">
                <div class="bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-center">
                    <span class="text-[9px] text-slate-400 uppercase font-bold block">Skor Disiplin</span>
                    <span id="eval-modal-score" class="text-lg font-black text-slate-800 mt-0.5 block">0</span>
                    <span id="eval-modal-badge" class="text-[9px] font-semibold text-emerald-600">-</span>
                </div>
                <div class="bg-teal-50/60 border border-teal-200 rounded-xl p-2.5 text-center">
                    <span class="text-[9px] text-teal-700 uppercase font-bold block">Kehadiran Pos</span>
                    <span id="eval-modal-att" class="text-lg font-black text-teal-800 mt-0.5 block">0x / 0</span>
                    <span id="eval-modal-att-pct" class="text-[9px] text-teal-600">0% hadir</span>
                </div>
                <div class="bg-rose-50/60 border border-rose-200 rounded-xl p-2.5 text-center">
                    <span class="text-[9px] text-rose-700 uppercase font-bold block">Mangkir (Alpha)</span>
                    <span id="eval-modal-missed" class="text-lg font-black text-rose-800 mt-0.5 block">0 sesi</span>
                    <span class="text-[9px] text-rose-600">Tidak checkin</span>
                </div>
                <div class="bg-amber-50/60 border border-amber-200 rounded-xl p-2.5 text-center">
                    <span class="text-[9px] text-amber-700 uppercase font-bold block">Terlambat</span>
                    <span id="eval-modal-late" class="text-lg font-black text-amber-800 mt-0.5 block">0x</span>
                    <span id="eval-modal-late-info" class="text-[9px] text-amber-600">Avg: 0m</span>
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
let currentStartDate = '';
let currentEndDate = '';

function applyCustomDateRange() {
    const s = document.getElementById('eval-start-date').value;
    const e = document.getElementById('eval-end-date').value;

    if (s && e && s > e) {
        alert('Tanggal Mulai tidak boleh lebih besar dari Tanggal Selesai.');
        return;
    }

    currentStartDate = s;
    currentEndDate = e;
    loadEvaluasiData();
}

function resetEvaluasiDateRange() {
    currentStartDate = '';
    currentEndDate = '';
    const inpStart = document.getElementById('eval-start-date');
    const inpEnd = document.getElementById('eval-end-date');
    if (inpStart) inpStart.value = '';
    if (inpEnd) inpEnd.value = '';
    loadEvaluasiData();
}

async function loadEvaluasiData() {
    try {
        let url = `/api/ops/evaluasi/summary?unit=${currentEvaluasiUnit}`;
        if (currentStartDate) url += `&start_date=${currentStartDate}`;
        if (currentEndDate) url += `&end_date=${currentEndDate}`;

        const res = await fetch(url);
        const data = await res.json();
        evaluasiDataCache = data;

        // Sinkronisasi value input date jika masih kosong
        const inpStart = document.getElementById('eval-start-date');
        const inpEnd = document.getElementById('eval-end-date');
        if (inpStart && !inpStart.value && data.start_date) {
            inpStart.value = data.start_date;
            currentStartDate = data.start_date;
        }
        if (inpEnd && !inpEnd.value && data.end_date) {
            inpEnd.value = data.end_date;
            currentEndDate = data.end_date;
        }

        // 1. Header Period Badge & Targets
        const periodBadge = document.getElementById('eval-header-period-badge');
        if (periodBadge) {
            periodBadge.innerText = `Periode: ${data.start_date} s.d. ${data.end_date}`;
        }
        document.getElementById('eval-target-ob-badge').innerText = data.target_sessions_ob || 0;
        document.getElementById('eval-target-gardener-badge').innerText = data.target_sessions_gardener || 0;

        // 2. KPI Cards
        document.getElementById('eval-stat-personnel').innerText = data.total_personnel || 0;
        document.getElementById('eval-stat-sessions-info').innerText = `Wajib: OB ${data.target_sessions_ob || 0} • Gardener ${data.target_sessions_gardener || 0}`;
        document.getElementById('eval-stat-attendance-rate').innerText = `${data.overall_attendance || 0}%`;
        document.getElementById('eval-stat-attendance-bar').style.width = `${data.overall_attendance || 0}%`;
        document.getElementById('eval-stat-checkins').innerText = `${data.total_checkins || 0} hadir`;
        document.getElementById('eval-stat-missed').innerText = data.total_missed || 0;
        document.getElementById('eval-stat-late').innerText = data.top_late?.reduce((a, b) => a + b.terlambat, 0) || 0;
        document.getElementById('eval-stat-late-pct').innerText = `${data.late_rate || 0}% dari sesi hadir`;

        // Update Export CSV Link
        const exportBtn = document.getElementById('eval-btn-export-csv');
        if (exportBtn) {
            exportBtn.href = `/export/evaluasi?unit=${currentEvaluasiUnit}&start_date=${data.start_date}&end_date=${data.end_date}`;
        }

        // 3. Render Widgets & Table
        renderEvaluasiWidgets(data.top_missed || [], data.top_late || [], data.top_out_radius || []);
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

function renderEvaluasiWidgets(topMissed, topLate, topRadius) {
    // 1. Top Missed Widget (Mangkir Pos / Alpha)
    const missedContainer = document.getElementById('eval-top-missed-container');
    if (missedContainer) {
        if (!topMissed.length) {
            missedContainer.innerHTML = '<p class="text-xs text-slate-400 py-3 text-center">Seluruh staf hadir 100% pada semua sesi pos! 👏</p>';
        } else {
            missedContainer.innerHTML = topMissed.slice(0, 5).map((p, idx) => {
                const missedPct = Math.round((p.missed_checkin / p.target_sessions) * 100);
                return `
                    <div class="p-2 bg-slate-50 hover:bg-rose-50/50 rounded-xl border border-slate-100 transition space-y-1">
                        <div class="flex items-center justify-between text-xs">
                            <div class="flex items-center gap-1.5">
                                <span class="w-4 h-4 rounded-full bg-rose-100 text-rose-800 flex items-center justify-center font-bold text-[9px]">${idx + 1}</span>
                                <span class="font-bold text-slate-800">${escapeHtml(p.nama)}</span>
                                <span class="text-[9px] text-slate-400">(${p.unit})</span>
                            </div>
                            <span class="font-bold text-rose-700 text-xs">${p.missed_checkin}x Mangkir</span>
                        </div>
                        <div class="w-full bg-slate-200 rounded-full h-1 overflow-hidden">
                            <div class="bg-rose-500 h-1 rounded-full" style="width: ${missedPct}%"></div>
                        </div>
                        <div class="flex items-center justify-between text-[9px] text-slate-500">
                            <span>Hadir: <strong class="text-teal-700">${p.total_checkin} / ${p.target_sessions} (${p.attendance_rate}%)</strong></span>
                            <button type="button" onclick="openModalEvaluasi('${escapeHtml(p.nama)}')" class="text-indigo-600 hover:text-indigo-800 font-bold cursor-pointer">Beri Arahan →</button>
                        </div>
                    </div>
                `;
            }).join('');
        }
    }

    // 2. Top Late Widget
    const lateContainer = document.getElementById('eval-top-late-container');
    if (lateContainer) {
        if (!topLate.length) {
            lateContainer.innerHTML = '<p class="text-xs text-slate-400 py-3 text-center">Tidak ada catatan keterlambatan pada periode ini. 👏</p>';
        } else {
            lateContainer.innerHTML = topLate.slice(0, 5).map((p, idx) => {
                const barWidth = Math.min(100, p.late_pct);
                return `
                    <div class="p-2 bg-slate-50 hover:bg-amber-50/50 rounded-xl border border-slate-100 transition space-y-1">
                        <div class="flex items-center justify-between text-xs">
                            <div class="flex items-center gap-1.5">
                                <span class="w-4 h-4 rounded-full bg-amber-100 text-amber-800 flex items-center justify-center font-bold text-[9px]">${idx + 1}</span>
                                <span class="font-bold text-slate-800">${escapeHtml(p.nama)}</span>
                                <span class="text-[9px] text-slate-400">(${p.unit})</span>
                            </div>
                            <span class="font-bold text-amber-700 text-xs">${p.terlambat}x Telat <span class="text-[9px] text-slate-400">(${p.late_pct}%)</span></span>
                        </div>
                        <div class="w-full bg-slate-200 rounded-full h-1 overflow-hidden">
                            <div class="bg-amber-500 h-1 rounded-full" style="width: ${barWidth}%"></div>
                        </div>
                        <div class="flex items-center justify-between text-[9px] text-slate-500">
                            <span>Rata-rata: <strong class="text-slate-700">${p.avg_late_min}m</strong> | Max: <strong class="text-rose-600">${p.max_late_min}m</strong></span>
                            <button type="button" onclick="openModalEvaluasi('${escapeHtml(p.nama)}')" class="text-indigo-600 hover:text-indigo-800 font-bold cursor-pointer">Periksa →</button>
                        </div>
                    </div>
                `;
            }).join('');
        }
    }

    // 3. Top Out-Radius Widget
    const radiusContainer = document.getElementById('eval-top-radius-container');
    if (radiusContainer) {
        if (!topRadius.length) {
            radiusContainer.innerHTML = '<p class="text-xs text-slate-400 py-3 text-center">Seluruh checkin berada di dalam radius pos. 🎯</p>';
        } else {
            radiusContainer.innerHTML = topRadius.slice(0, 5).map((p, idx) => {
                const barWidth = Math.min(100, p.out_radius_pct);
                return `
                    <div class="p-2 bg-slate-50 hover:bg-purple-50/50 rounded-xl border border-slate-100 transition space-y-1">
                        <div class="flex items-center justify-between text-xs">
                            <div class="flex items-center gap-1.5">
                                <span class="w-4 h-4 rounded-full bg-purple-100 text-purple-800 flex items-center justify-center font-bold text-[9px]">${idx + 1}</span>
                                <span class="font-bold text-slate-800">${escapeHtml(p.nama)}</span>
                                <span class="text-[9px] text-slate-400">(${p.unit})</span>
                            </div>
                            <span class="font-bold text-purple-700 text-xs">${p.diluar_radius}x Luar <span class="text-[9px] text-slate-400">(${p.out_radius_pct}%)</span></span>
                        </div>
                        <div class="w-full bg-slate-200 rounded-full h-1 overflow-hidden">
                            <div class="bg-purple-500 h-1 rounded-full" style="width: ${barWidth}%"></div>
                        </div>
                        <div class="flex items-center justify-between text-[9px] text-slate-500">
                            <span>Avg: <strong class="text-slate-700">${p.avg_dist}m</strong> | Terjauh: <strong class="text-rose-600">${p.max_dist}m</strong></span>
                            <button type="button" onclick="openModalEvaluasi('${escapeHtml(p.nama)}')" class="text-indigo-600 hover:text-indigo-800 font-bold cursor-pointer">Lokasi →</button>
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
        tbody.innerHTML = '<tr><td colspan="14" class="text-center py-8 text-slate-400">Tidak ada personil yang sesuai dengan filter.</td></tr>';
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
                
                <!-- Target Sesi Wajib Unit -->
                <td class="py-2.5 px-2 text-center font-bold text-slate-600 bg-slate-50">${p.target_sessions}</td>

                <!-- Realisasi Hadir Check-in -->
                <td class="py-2.5 px-2 text-center font-bold text-teal-700">${p.total_checkin}x</td>

                <!-- Mangkir Pos (Alpha / Tidak Checkin) -->
                <td class="py-2.5 px-2 text-center bg-rose-50/50">
                    <span class="font-black ${p.missed_checkin > 5 ? 'text-rose-700' : (p.missed_checkin > 0 ? 'text-amber-700' : 'text-slate-400')} block">${p.missed_checkin} sesi</span>
                    <span class="text-[9px] text-rose-500">${Math.round((p.missed_checkin / p.target_sessions) * 100)}% bolos</span>
                </td>

                <!-- Kehadiran % -->
                <td class="py-2.5 px-3 text-center">
                    <span class="font-bold ${p.attendance_rate >= 80 ? 'text-teal-700' : (p.attendance_rate >= 60 ? 'text-amber-700' : 'text-rose-700')} block">${p.attendance_rate}%</span>
                    <div class="w-12 bg-slate-200 rounded-full h-1 mx-auto mt-0.5 overflow-hidden">
                        <div class="bg-teal-600 h-1 rounded-full" style="width: ${p.attendance_rate}%"></div>
                    </div>
                </td>

                <!-- Tepat Waktu -->
                <td class="py-2.5 px-3 text-center">
                    <span class="font-semibold text-slate-800 block">${p.tepat_waktu}x</span>
                    <span class="text-[10px] text-teal-600">(${p.on_time_pct}%)</span>
                </td>

                <!-- Terlambat -->
                <td class="py-2.5 px-3 text-center">
                    <span class="font-semibold ${p.terlambat > 0 ? 'text-amber-700' : 'text-slate-400'} block">${p.terlambat}x</span>
                    <span class="text-[10px] text-amber-600">(${p.late_pct}%)</span>
                </td>

                <!-- Luar Radius -->
                <td class="py-2.5 px-3 text-center">
                    <span class="font-semibold ${p.diluar_radius > 0 ? 'text-purple-700' : 'text-slate-400'} block">${p.diluar_radius}x</span>
                    <span class="text-[10px] text-purple-600">(${p.out_radius_pct}%)</span>
                </td>

                <!-- Skor Disiplin -->
                <td class="py-2.5 px-3 text-center">
                    <span class="text-sm font-black ${scoreColor} block">${p.discipline_score}</span>
                    <div class="w-16 bg-slate-200 rounded-full h-1 mx-auto mt-1 overflow-hidden">
                        <div class="bg-indigo-600 h-1 rounded-full" style="width: ${p.discipline_score}%"></div>
                    </div>
                </td>

                <!-- Status Rapor -->
                <td class="py-2.5 px-3 text-center">
                    <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${badgeStyle} inline-block whitespace-nowrap">${p.eval_badge}</span>
                </td>

                <!-- Catatan Supervisi -->
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
    document.getElementById('eval-modal-unit-badge').innerText = `Unit: ${p.unit} • Kewajiban Unit: ${p.target_sessions} Sesi (${p.days_active} hari kerja aktif)`;
    document.getElementById('eval-modal-score').innerText = p.discipline_score;
    document.getElementById('eval-modal-badge').innerText = p.eval_badge;
    document.getElementById('eval-modal-att').innerText = `${p.total_checkin}x / ${p.target_sessions}`;
    document.getElementById('eval-modal-att-pct').innerText = `${p.attendance_rate}% hadir pos`;
    document.getElementById('eval-modal-missed').innerText = `${p.missed_checkin} sesi`;
    document.getElementById('eval-modal-late').innerText = `${p.terlambat}x`;
    document.getElementById('eval-modal-late-info').innerText = `Avg: ${p.avg_late_min}m`;
    document.getElementById('eval-modal-rec').innerText = p.recommendation;

    // Render late list
    const lateList = document.getElementById('eval-modal-late-list');
    if (!p.late_details || !p.late_details.length) {
        lateList.innerHTML = '<p class="text-slate-400 italic">Tidak ada catatan keterlambatan terbaru pada rentang ini.</p>';
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
