"""
Templates & Komponen Tampilan HTML/JS untuk Modul Laporan & Evaluasi Mutaba'ah Petugas
An Nahl Ops Web Dashboard - note-umum.ametriyadhi.com
Model Subview: Radar Kepatuhan Harian, Riwayat Log Transaksi, dan Rapor Kedisiplinan Tim
"""

TAB_MUTABAAH_HTML = """
<!-- TAB LAPORAN & EVALUASI MUTABA'AH PETUGAS (OB, GARDENER, SECURITY) -->
<div id="tab-mutabaah" class="tab-content hidden space-y-6">

    <!-- Header & Action Bar -->
    <div class="bg-white rounded-2xl shadow-xs border border-slate-200/80 p-4 sm:p-6 space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
            <div>
                <div class="flex items-center gap-2">
                    <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-teal-100 text-teal-800 tracking-wider uppercase">Pusat Evaluasi Ibadah</span>
                    <span id="mutabaah-header-period-badge" class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 uppercase tracking-wider">Hari Ini</span>
                </div>
                <h2 class="text-base sm:text-xl font-bold text-slate-800 flex items-center gap-2 mt-1">
                    <i class="fa-solid fa-kaaba text-teal-600"></i>
                    Laporan & Evaluasi Mutaba'ah Petugas Lapangan
                </h2>
                <p class="text-xs text-slate-500 mt-0.5">Pemantauan kepatuhan ibadah yaumiyah (Sholat 5 Waktu, Tilawah Al-Qur'an, Dzikir Pagi/Petang) tim Office Boy (OB), Gardener & Security.</p>
            </div>
            <div class="flex items-center gap-2 sm:gap-3 flex-wrap">
                <button type="button" onclick="refreshMutabaahActiveView()" class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition flex items-center gap-1.5 cursor-pointer">
                    <i class="fa-solid fa-arrows-rotate"></i> Refresh
                </button>
                <button type="button" onclick="openModalMutabaahGuide()" class="px-3 py-1.5 bg-sky-50 hover:bg-sky-100 text-sky-700 border border-sky-200 text-xs font-semibold rounded-lg transition flex items-center gap-1.5 cursor-pointer">
                    <i class="fa-brands fa-whatsapp text-emerald-600"></i> Format WA
                </button>
                <button type="button" onclick="exportMutabaahExcel()" class="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-lg transition shadow-xs flex items-center gap-1.5 cursor-pointer">
                    <i class="fa-solid fa-file-excel"></i> Ekspor Excel (2-Sheet)
                </button>
            </div>
        </div>

        <!-- Metric Summary Cards -->
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
            <div class="bg-slate-50 border border-slate-200/90 rounded-xl p-3 sm:p-4">
                <span class="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">Total Petugas</span>
                <div class="flex items-baseline gap-2 mt-0.5">
                    <span id="stat-mutabaah-total" class="text-xl sm:text-2xl font-black text-slate-800">0</span>
                    <span class="text-[11px] font-medium text-slate-400">personel</span>
                </div>
                <span id="stat-mutabaah-unit-label" class="text-[10px] text-slate-400 block mt-0.5">Office Boy (OB) An Nahl</span>
            </div>

            <div class="bg-emerald-50 border border-emerald-200 rounded-xl p-3 sm:p-4">
                <span class="text-[11px] font-bold text-emerald-700 uppercase tracking-wider block">🟢 Sudah Lapor Hari Ini</span>
                <div class="flex items-baseline gap-2 mt-0.5">
                    <span id="stat-mutabaah-reported" class="text-xl sm:text-2xl font-black text-emerald-700">0</span>
                    <span id="stat-mutabaah-pct" class="text-xs font-bold text-emerald-600">(0%)</span>
                </div>
                <span class="text-[10px] text-emerald-600 block mt-0.5">Tercatat di bot operasional</span>
            </div>

            <div class="bg-rose-50 border border-rose-200 rounded-xl p-3 sm:p-4">
                <span class="text-[11px] font-bold text-rose-700 uppercase tracking-wider block">🔴 Belum Lapor Hari Ini</span>
                <div class="flex items-baseline gap-2 mt-0.5">
                    <span id="stat-mutabaah-unreported" class="text-xl sm:text-2xl font-black text-rose-700">0</span>
                    <span class="text-[11px] font-medium text-rose-500">petugas</span>
                </div>
                <span class="text-[10px] text-rose-600 block mt-0.5">Perlu diingatkan via WhatsApp</span>
            </div>

            <div class="bg-teal-50 border border-teal-200 rounded-xl p-3 sm:p-4">
                <span class="text-[11px] font-bold text-teal-700 uppercase tracking-wider block">📖 Tilawah & Sholat 5 Waktu</span>
                <div class="flex items-baseline gap-2 mt-0.5">
                    <span id="stat-mutabaah-ibadah" class="text-xl sm:text-2xl font-black text-teal-700">0</span>
                    <span class="text-[11px] font-medium text-teal-600">aktif</span>
                </div>
                <span id="stat-mutabaah-ibadah-sub" class="text-[10px] text-teal-600 block mt-0.5">Lengkap Sholat & Al-Qur'an</span>
            </div>
        </div>

        <!-- Filter & Sub-Nav Bar -->
        <div class="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-slate-50 p-2.5 sm:p-3 rounded-xl border border-slate-200 text-xs">
            <!-- Filter Unit -->
            <div class="flex items-center gap-2 flex-wrap">
                <label class="text-slate-600 font-bold shrink-0 flex items-center gap-1">
                    <i class="fa-solid fa-users text-teal-600"></i> Unit Kerja:
                </label>
                <select id="filter-mutabaah-unit" onchange="onMutabaahUnitChange()" class="bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 font-semibold focus:outline-none focus:ring-1 focus:ring-teal-500 shadow-2xs">
                    <option value="OB" selected>Office Boy (OB)</option>
                    <option value="GARDENER">Gardener (Taman & Ecopark)</option>
                    <option value="SECURITY">Security (Keamanan)</option>
                    <option value="ALL">Semua Unit (OB, Gardener, Security)</option>
                </select>

                <!-- Filter Tanggal Harian untuk Radar -->
                <div id="wrapper-mutabaah-date" class="flex items-center gap-1.5 ml-0 sm:ml-2">
                    <label class="text-slate-500 font-medium shrink-0">Tanggal:</label>
                    <input type="date" id="filter-mutabaah-radar-date" onchange="loadMutabaahRadar()" class="bg-white border border-slate-300 rounded-lg px-2.5 py-1 text-xs text-slate-800 font-semibold focus:outline-none focus:ring-1 focus:ring-teal-500 shadow-2xs">
                </div>
            </div>

            <!-- View Switcher Tabs (Model Persis Tab Standby) -->
            <div class="flex items-center space-x-1 bg-white p-1 rounded-lg border border-slate-200 shadow-2xs shrink-0">
                <button type="button" onclick="switchMutabaahSubView('radar')" id="btn-mutabaah-subview-radar" class="px-3 py-1.5 rounded-md font-bold text-teal-700 bg-teal-50 shadow-2xs border border-teal-200 cursor-pointer transition">
                    <i class="fa-solid fa-radar mr-1 text-teal-600"></i> Radar Hari Ini
                </button>
                <button type="button" onclick="switchMutabaahSubView('logs')" id="btn-mutabaah-subview-logs" class="px-3 py-1.5 rounded-md font-semibold text-slate-600 hover:text-slate-900 cursor-pointer transition">
                    <i class="fa-solid fa-clock-rotate-left mr-1 text-indigo-600"></i> Riwayat Log
                </button>
                <button type="button" onclick="switchMutabaahSubView('evaluasi')" id="btn-mutabaah-subview-evaluasi" class="px-3 py-1.5 rounded-md font-semibold text-slate-600 hover:text-slate-900 cursor-pointer transition">
                    <i class="fa-solid fa-chart-line mr-1 text-emerald-600"></i> Rapor Kedisiplinan
                </button>
            </div>
        </div>
    </div>

    <!-- ================================================================= -->
    <!-- SUBVIEW 1: RADAR KEPATUHAN MUTABA'AH HARI INI                     -->
    <!-- ================================================================= -->
    <div id="mutabaah-subview-radar" class="space-y-4">
        <div class="bg-white rounded-xl shadow-xs border border-slate-200 overflow-hidden">
            <div class="p-4 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-2 bg-slate-50/50">
                <div>
                    <h3 class="font-bold text-sm text-slate-800 flex items-center gap-2">
                        <i class="fa-solid fa-satellite-dish text-teal-600"></i>
                        Radar Kepatuhan Mutaba'ah Petugas (<span id="radar-display-date">Hari Ini</span>)
                    </h3>
                    <p class="text-[11px] text-slate-500">Daftar personil tugas dan konfirmasi laporan ibadah harian yang masuk ke WhatsApp Bot.</p>
                </div>
                <div class="flex items-center gap-2 text-xs">
                    <span class="inline-flex items-center gap-1 px-2 py-0.5 bg-emerald-100 text-emerald-800 font-bold rounded text-[10px]">
                        <span class="w-2 h-2 rounded-full bg-emerald-500"></span> Sudah Lapor
                    </span>
                    <span class="inline-flex items-center gap-1 px-2 py-0.5 bg-rose-100 text-rose-800 font-bold rounded text-[10px]">
                        <span class="w-2 h-2 rounded-full bg-rose-500 animate-pulse"></span> Belum Lapor
                    </span>
                </div>
            </div>

            <div class="overflow-x-auto">
                <table class="w-full text-left text-xs">
                    <thead class="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                        <tr>
                            <th class="py-3 px-3 text-center w-10">No</th>
                            <th class="py-3 px-3">Nama Petugas</th>
                            <th class="py-3 px-3">Unit & Tugas</th>
                            <th class="py-3 px-3">No. WhatsApp</th>
                            <th class="py-3 px-3 text-center">Status Lapor</th>
                            <th class="py-3 px-3">Jam Masuk</th>
                            <th class="py-3 px-3">Sholat</th>
                            <th class="py-3 px-3">Tilawah Al-Qur'an</th>
                            <th class="py-3 px-3">Dzikir</th>
                            <th class="py-3 px-3 text-center">Tindak Lanjut</th>
                        </tr>
                    </thead>
                    <tbody id="mutabaah-radar-tbody" class="divide-y divide-slate-100">
                        <tr><td colspan="10" class="text-center py-8 text-slate-400"><i class="fa-solid fa-spinner fa-spin mr-2"></i>Memuat radar kepatuhan...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- ================================================================= -->
    <!-- SUBVIEW 2: RIWAYAT LOG TRANSAKSI MUTABA'AH LENGKAP               -->
    <!-- ================================================================= -->
    <div id="mutabaah-subview-logs" class="hidden space-y-4">
        <div class="bg-white rounded-xl shadow-xs border border-slate-200 p-4 sm:p-6 space-y-4">
            
            <!-- Filter Bar Riwayat Log -->
            <div class="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-3 bg-slate-50 p-3 rounded-xl border border-slate-200 text-xs">
                
                <!-- Rentang Tanggal & Preset -->
                <div class="flex items-center gap-2 flex-wrap">
                    <span class="font-bold text-slate-700 flex items-center gap-1">
                        <i class="fa-regular fa-calendar-days text-teal-600"></i> Periode:
                    </span>
                    <input type="date" id="mutabaah-log-start" onchange="loadMutabaahLogs()" class="bg-white border border-slate-300 rounded-lg px-2.5 py-1 text-xs text-slate-800 font-semibold">
                    <span class="text-slate-400">s/d</span>
                    <input type="date" id="mutabaah-log-end" onchange="loadMutabaahLogs()" class="bg-white border border-slate-300 rounded-lg px-2.5 py-1 text-xs text-slate-800 font-semibold">
                    
                    <!-- Shortcut Presets -->
                    <div class="inline-flex rounded-lg border border-slate-200 bg-white p-0.5 shadow-2xs">
                        <button type="button" onclick="setMutabaahLogPreset('today')" class="px-2 py-0.5 text-[11px] font-semibold text-slate-600 hover:text-teal-700 hover:bg-slate-50 rounded cursor-pointer">Hari Ini</button>
                        <button type="button" onclick="setMutabaahLogPreset('yesterday')" class="px-2 py-0.5 text-[11px] font-semibold text-slate-600 hover:text-teal-700 hover:bg-slate-50 rounded cursor-pointer">Kemarin</button>
                        <button type="button" onclick="setMutabaahLogPreset('7days')" class="px-2 py-0.5 text-[11px] font-semibold text-slate-600 hover:text-teal-700 hover:bg-slate-50 rounded cursor-pointer">7 Hari</button>
                        <button type="button" onclick="setMutabaahLogPreset('month')" class="px-2 py-0.5 text-[11px] font-semibold text-teal-700 font-bold bg-teal-50 rounded cursor-pointer">Bulan Ini</button>
                        <button type="button" onclick="setMutabaahLogPreset('all')" class="px-2 py-0.5 text-[11px] font-semibold text-slate-600 hover:text-teal-700 hover:bg-slate-50 rounded cursor-pointer">Semua</button>
                    </div>
                </div>

                <!-- Live Search Box -->
                <div class="relative w-full lg:w-72">
                    <i class="fa-solid fa-magnifying-glass absolute left-3 top-2.5 text-slate-400 text-xs"></i>
                    <input type="text" id="mutabaah-log-search" onkeyup="loadMutabaahLogsDebounced()" placeholder="Cari nama, tilawah, surah..." class="w-full pl-8 pr-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-teal-500 shadow-2xs">
                </div>
            </div>

            <!-- Header Total & Export -->
            <div class="flex items-center justify-between text-xs text-slate-500 px-1">
                <span id="mutabaah-logs-counter" class="font-bold text-slate-700">Menampilkan 0 catatan</span>
                <span class="text-[11px] text-slate-400">Sumber data: mutabaah_logs.json</span>
            </div>

            <!-- Tabel Log Transaksi -->
            <div class="overflow-x-auto border border-slate-200 rounded-xl">
                <table class="w-full text-left text-xs">
                    <thead class="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                        <tr>
                            <th class="py-3 px-3 w-28">Waktu (WIB)</th>
                            <th class="py-3 px-3">Nama Petugas</th>
                            <th class="py-3 px-3">Unit</th>
                            <th class="py-3 px-3">Sholat</th>
                            <th class="py-3 px-3">Tilawah Al-Qur'an</th>
                            <th class="py-3 px-3">Dzikir</th>
                            <th class="py-3 px-3 text-center w-24">Teks Pesan</th>
                        </tr>
                    </thead>
                    <tbody id="mutabaah-logs-tbody" class="divide-y divide-slate-100">
                        <tr><td colspan="7" class="text-center py-8 text-slate-400"><i class="fa-solid fa-spinner fa-spin mr-2"></i>Memuat riwayat log...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- ================================================================= -->
    <!-- SUBVIEW 3: RAPOR & EVALUASI KEDISIPLINAN TIM                      -->
    <!-- ================================================================= -->
    <div id="mutabaah-subview-evaluasi" class="hidden space-y-4">
        <div class="bg-white rounded-xl shadow-xs border border-slate-200 p-4 sm:p-6 space-y-4">
            
            <!-- Filter Bar Evaluasi -->
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-50 p-3 rounded-xl border border-slate-200 text-xs">
                <div class="flex items-center gap-2 flex-wrap">
                    <span class="font-bold text-slate-700 flex items-center gap-1.5">
                        <i class="fa-solid fa-calendar-check text-emerald-600"></i> Periode Evaluasi:
                    </span>
                    <input type="date" id="mutabaah-eval-start" onchange="loadMutabaahEvaluasi()" class="bg-white border border-slate-300 rounded-lg px-2.5 py-1 text-xs text-slate-800 font-semibold">
                    <span class="text-slate-400">s/d</span>
                    <input type="date" id="mutabaah-eval-end" onchange="loadMutabaahEvaluasi()" class="bg-white border border-slate-300 rounded-lg px-2.5 py-1 text-xs text-slate-800 font-semibold">
                    <button type="button" onclick="loadMutabaahEvaluasi()" class="px-3 py-1 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-lg transition cursor-pointer">
                        Hitung Rapor
                    </button>
                </div>
                <div class="text-[11px] text-slate-500 font-medium">
                    Total Hari Kalender: <strong id="eval-total-days" class="text-slate-800 font-bold">0 Hari</strong>
                </div>
            </div>

            <!-- Petunjuk Skala Penilaian Disiplin -->
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px]">
                <div class="bg-emerald-50 border border-emerald-200 rounded-lg p-2 flex items-center gap-2">
                    <span class="w-3 h-3 rounded-full bg-emerald-500 shrink-0"></span>
                    <div>
                        <strong class="text-emerald-800 block">Sangat Disiplin (A)</strong>
                        <span class="text-emerald-600 text-[10px]">Kepatuhan ≥ 85%</span>
                    </div>
                </div>
                <div class="bg-sky-50 border border-sky-200 rounded-lg p-2 flex items-center gap-2">
                    <span class="w-3 h-3 rounded-full bg-sky-500 shrink-0"></span>
                    <div>
                        <strong class="text-sky-800 block">Disiplin (B)</strong>
                        <span class="text-sky-600 text-[10px]">Kepatuhan 70% – 84%</span>
                    </div>
                </div>
                <div class="bg-amber-50 border border-amber-200 rounded-lg p-2 flex items-center gap-2">
                    <span class="w-3 h-3 rounded-full bg-amber-500 shrink-0"></span>
                    <div>
                        <strong class="text-amber-800 block">Cukup (C)</strong>
                        <span class="text-amber-600 text-[10px]">Kepatuhan 50% – 69%</span>
                    </div>
                </div>
                <div class="bg-rose-50 border border-rose-200 rounded-lg p-2 flex items-center gap-2">
                    <span class="w-3 h-3 rounded-full bg-rose-500 shrink-0"></span>
                    <div>
                        <strong class="text-rose-800 block">Perlu Pembinaan (D)</strong>
                        <span class="text-rose-600 text-[10px]">Kepatuhan < 50%</span>
                    </div>
                </div>
            </div>

            <!-- Tabel Rapor Kedisiplinan -->
            <div class="overflow-x-auto border border-slate-200 rounded-xl">
                <table class="w-full text-left text-xs">
                    <thead class="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                        <tr>
                            <th class="py-3 px-3 text-center w-10">Rank</th>
                            <th class="py-3 px-3">Nama Petugas</th>
                            <th class="py-3 px-3">Unit & Tugas</th>
                            <th class="py-3 px-3 text-center">Hari Lapor</th>
                            <th class="py-3 px-3 w-44">Tingkat Kepatuhan</th>
                            <th class="py-3 px-3 text-center">Sholat 5 Waktu</th>
                            <th class="py-3 px-3 text-center">Tilawah</th>
                            <th class="py-3 px-3 text-center">Dzikir</th>
                            <th class="py-3 px-3 text-center">Predikat Karakter</th>
                            <th class="py-3 px-3 text-center">Lapor Terakhir</th>
                        </tr>
                    </thead>
                    <tbody id="mutabaah-eval-tbody" class="divide-y divide-slate-100">
                        <tr><td colspan="10" class="text-center py-8 text-slate-400"><i class="fa-solid fa-spinner fa-spin mr-2"></i>Memuat rapor kedisiplinan...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

</div>

<!-- MODAL POPUP: DETAIL PESAN WHATSAPP VERBATIM -->
<div id="modal-mutabaah-detail" class="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 hidden">
    <div class="bg-white rounded-2xl shadow-xl border border-slate-200 w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <div class="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
            <h3 class="font-bold text-sm text-slate-800 flex items-center gap-2">
                <i class="fa-brands fa-whatsapp text-emerald-600 text-base"></i>
                <span id="modal-detail-petugas-name">Pesan Mutaba'ah Petugas</span>
            </h3>
            <button onclick="closeModalMutabaahDetail()" class="text-slate-400 hover:text-slate-600 p-1 text-sm cursor-pointer">
                <i class="fa-solid fa-xmark"></i>
            </button>
        </div>
        <div class="p-5 space-y-3">
            <div class="text-[11px] text-slate-500 font-medium">
                Tanggal Lapor: <span id="modal-detail-date" class="font-bold text-slate-700">-</span>
            </div>
            <div class="bg-slate-900 text-emerald-400 p-3.5 rounded-xl font-mono text-xs whitespace-pre-wrap max-h-64 overflow-y-auto leading-relaxed border border-slate-800" id="modal-detail-raw-text">
                -
            </div>
        </div>
        <div class="p-3.5 bg-slate-50 border-t border-slate-100 flex justify-end">
            <button onclick="closeModalMutabaahDetail()" class="px-4 py-1.5 bg-slate-200 hover:bg-slate-300 text-slate-700 text-xs font-semibold rounded-lg transition cursor-pointer">
                Tutup
            </button>
        </div>
    </div>
</div>

<!-- MODAL POPUP: PANDUAN FORMAT MUTABAAH WHATSAPP -->
<div id="modal-mutabaah-guide" class="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 hidden">
    <div class="bg-white rounded-2xl shadow-xl border border-slate-200 w-full max-w-lg overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <div class="p-4 border-b border-slate-100 flex items-center justify-between bg-emerald-50 text-emerald-900">
            <h3 class="font-bold text-sm flex items-center gap-2">
                <i class="fa-solid fa-book-quran text-emerald-600 text-base"></i>
                Panduan Format Mutaba'ah Yaumiyah WhatsApp
            </h3>
            <button onclick="closeModalMutabaahGuide()" class="text-emerald-700 hover:text-emerald-900 p-1 text-sm cursor-pointer">
                <i class="fa-solid fa-xmark"></i>
            </button>
        </div>
        <div class="p-5 space-y-4 text-xs text-slate-700">
            <p>Petugas operasional (OB, Gardener, Security) dapat mengirimkan laporan mutaba'ah harian ke nomor WhatsApp Bot Operasional (<strong>0851-3937-3029</strong>) atau di grup operasional setiap sore hari (sebelum jam 17:30 WIB).</p>

            <div class="bg-slate-50 border border-slate-200 rounded-xl p-3 space-y-2">
                <span class="font-bold text-slate-800 block text-[11px] uppercase tracking-wider">Format Standar Pesan:</span>
                <pre class="bg-white p-3 rounded-lg border border-slate-200 font-mono text-emerald-700 text-[11px] leading-relaxed">Mutabaah
Nama: [Nama Lengkap]
Unit: [OB / Gardener / Security]
Sholat: 5 waktu
Tilawah: [Nama Surah & Ayat / Juz]
Dzikir: pagi petang</pre>
            </div>

            <div class="space-y-1 text-slate-600 text-[11px]">
                <div class="flex items-start gap-2">
                    <i class="fa-solid fa-circle-check text-emerald-600 mt-0.5"></i>
                    <span>Bot otomatis mencatat tanggal, jam masuk, dan mengagregasi kepatuhan ke dashboard note-umum.</span>
                </div>
                <div class="flex items-start gap-2">
                    <i class="fa-solid fa-circle-check text-emerald-600 mt-0.5"></i>
                    <span>Toleransi teks: Bot menerima variasi ejaan huruf besar/kecil dan spasi.</span>
                </div>
            </div>
        </div>
        <div class="p-3.5 bg-slate-50 border-t border-slate-100 flex justify-end">
            <button onclick="closeModalMutabaahGuide()" class="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-lg transition cursor-pointer">
                Mengerti
            </button>
        </div>
    </div>
</div>
"""

MUTABAAH_CLIENT_SCRIPT = """
<script>
// =========================================================================
// JAVASCRIPT LOGIC UNTUK TAB LAPORAN & EVALUASI MUTABA'AH (OB & LAPANGAN)
// =========================================================================

let currentMutabaahSubView = 'radar';
let mutabaahSearchTimer = null;

function initMutabaahTab() {
    const today = new Date();
    const y = today.getFullYear();
    const m = String(today.getMonth() + 1).padStart(2, '0');
    const d = String(today.getDate()).padStart(2, '0');
    const todayStr = `${y}-${m}-${d}`;

    const radarDateInput = document.getElementById('filter-mutabaah-radar-date');
    if (radarDateInput && !radarDateInput.value) {
        radarDateInput.value = todayStr;
    }

    const logStartInput = document.getElementById('mutabaah-log-start');
    const logEndInput = document.getElementById('mutabaah-log-end');
    if (logStartInput && !logStartInput.value) {
        // Default log: 30 hari terakhir
        const prev30 = new Date(today);
        prev30.setDate(prev30.getDate() - 29);
        const y30 = prev30.getFullYear();
        const m30 = String(prev30.getMonth() + 1).padStart(2, '0');
        const d30 = String(prev30.getDate()).padStart(2, '0');
        logStartInput.value = `${y30}-${m30}-${d30}`;
        logEndInput.value = todayStr;
    }

    const evalStartInput = document.getElementById('mutabaah-eval-start');
    const evalEndInput = document.getElementById('mutabaah-eval-end');
    if (evalStartInput && !evalStartInput.value) {
        // Default evaluasi: bulan berjalan
        const firstDay = `${y}-${m}-01`;
        evalStartInput.value = firstDay;
        evalEndInput.value = todayStr;
    }

    loadMutabaahRadar();
}

function onMutabaahUnitChange() {
    const unit = document.getElementById('filter-mutabaah-unit').value;
    const label = document.getElementById('stat-mutabaah-unit-label');
    if (label) {
        if (unit === 'OB') label.innerText = 'Office Boy (OB) An Nahl';
        else if (unit === 'GARDENER') label.innerText = 'Gardener / Pertamanan & Ecopark';
        else if (unit === 'SECURITY') label.innerText = 'Security / Keamanan & Ketertiban';
        else label.innerText = 'Semua Unit Operasional (OB, Gardener, Security)';
    }

    refreshMutabaahActiveView();
}

function switchMutabaahSubView(view) {
    currentMutabaahSubView = view;

    const subRadar = document.getElementById('mutabaah-subview-radar');
    const subLogs = document.getElementById('mutabaah-subview-logs');
    const subEval = document.getElementById('mutabaah-subview-evaluasi');

    const btnRadar = document.getElementById('btn-mutabaah-subview-radar');
    const btnLogs = document.getElementById('btn-mutabaah-subview-logs');
    const btnEval = document.getElementById('btn-mutabaah-subview-evaluasi');

    const wrapperDate = document.getElementById('wrapper-mutabaah-date');

    subRadar.classList.add('hidden');
    subLogs.classList.add('hidden');
    subEval.classList.add('hidden');

    btnRadar.className = "px-3 py-1.5 rounded-md font-semibold text-slate-600 hover:text-slate-900 cursor-pointer transition";
    btnLogs.className = "px-3 py-1.5 rounded-md font-semibold text-slate-600 hover:text-slate-900 cursor-pointer transition";
    btnEval.className = "px-3 py-1.5 rounded-md font-semibold text-slate-600 hover:text-slate-900 cursor-pointer transition";

    if (view === 'radar') {
        subRadar.classList.remove('hidden');
        btnRadar.className = "px-3 py-1.5 rounded-md font-bold text-teal-700 bg-teal-50 shadow-2xs border border-teal-200 cursor-pointer transition";
        if (wrapperDate) wrapperDate.classList.remove('hidden');
        loadMutabaahRadar();
    } else if (view === 'logs') {
        subLogs.classList.remove('hidden');
        btnLogs.className = "px-3 py-1.5 rounded-md font-bold text-indigo-700 bg-indigo-50 shadow-2xs border border-indigo-200 cursor-pointer transition";
        if (wrapperDate) wrapperDate.classList.add('hidden');
        loadMutabaahLogs();
    } else if (view === 'evaluasi') {
        subEval.classList.remove('hidden');
        btnEval.className = "px-3 py-1.5 rounded-md font-bold text-emerald-700 bg-emerald-50 shadow-2xs border border-emerald-200 cursor-pointer transition";
        if (wrapperDate) wrapperDate.classList.add('hidden');
        loadMutabaahEvaluasi();
    }
}

function refreshMutabaahActiveView() {
    if (currentMutabaahSubView === 'radar') {
        loadMutabaahRadar();
    } else if (currentMutabaahSubView === 'logs') {
        loadMutabaahLogs();
    } else if (currentMutabaahSubView === 'evaluasi') {
        loadMutabaahEvaluasi();
    }
}

// -------------------------------------------------------------------------
// 1. RADAR KEPATUHAN MUTABA'AH HARI INI
// -------------------------------------------------------------------------
function loadMutabaahRadar() {
    const tbody = document.getElementById('mutabaah-radar-tbody');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="10" class="text-center py-8 text-slate-400"><i class="fa-solid fa-spinner fa-spin mr-2"></i>Memuat radar kepatuhan mutabaah...</td></tr>';

    const unit = document.getElementById('filter-mutabaah-unit') ? document.getElementById('filter-mutabaah-unit').value : 'OB';
    const date = document.getElementById('filter-mutabaah-radar-date') ? document.getElementById('filter-mutabaah-radar-date').value : '';

    const displayDateEl = document.getElementById('radar-display-date');
    if (displayDateEl) {
        displayDateEl.innerText = date || 'Hari Ini';
    }

    const url = `/api/ops/mutabaah/radar?unit=${encodeURIComponent(unit)}&date=${encodeURIComponent(date)}`;

    fetch(url)
        .then(r => r.json())
        .then(data => {
            if (!data.success) throw new Error(data.error || 'Gagal memuat radar');

            const s = data.summary;
            document.getElementById('stat-mutabaah-total').innerText = s.total_personnel;
            document.getElementById('stat-mutabaah-reported').innerText = s.reported_count;
            document.getElementById('stat-mutabaah-pct').innerText = `(${s.compliance_pct}%)`;
            document.getElementById('stat-mutabaah-unreported').innerText = s.unreported_count;
            document.getElementById('stat-mutabaah-ibadah').innerText = `${s.sholat_5_count} Sholat / ${s.tilawah_count} Tilawah`;

            const periodBadge = document.getElementById('mutabaah-header-period-badge');
            if (periodBadge) periodBadge.innerText = data.date;

            if (!data.radar || data.radar.length === 0) {
                tbody.innerHTML = '<tr><td colspan="10" class="text-center py-8 text-slate-400">Tidak ada personil terdaftar untuk filter ini.</td></tr>';
                return;
            }

            let html = '';
            data.radar.forEach((item, idx) => {
                const p = item.personnel;
                const reported = item.has_reported;

                let statusBadge = '';
                let actionBtn = '';

                if (reported) {
                    statusBadge = `<span class="px-2.5 py-1 bg-emerald-100 text-emerald-800 text-[10px] font-bold rounded-full border border-emerald-300 inline-flex items-center gap-1">
                        <i class="fa-solid fa-circle-check"></i> Sudah Lapor
                    </span>`;
                    
                    const safeRaw = encodeURIComponent(item.raw_text || '');
                    actionBtn = `<button onclick="showMutabaahRawText('${p.name}', '${data.date}', decodeURIComponent('${safeRaw}'))" class="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 text-[11px] font-semibold rounded-lg transition inline-flex items-center gap-1 cursor-pointer" title="Lihat Teks WA Asli">
                        <i class="fa-regular fa-message text-teal-600"></i> Detail
                    </button>`;
                } else {
                    statusBadge = `<span class="px-2.5 py-1 bg-rose-100 text-rose-800 text-[10px] font-bold rounded-full border border-rose-300 inline-flex items-center gap-1">
                        <i class="fa-solid fa-clock-rotate-left animate-pulse"></i> Belum Lapor
                    </span>`;

                    if (item.wa_reminder_link) {
                        actionBtn = `<a href="${item.wa_reminder_link}" target="_blank" class="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white text-[11px] font-bold rounded-lg transition inline-flex items-center gap-1 shadow-2xs" title="Kirim Pengingat WhatsApp">
                            <i class="fa-brands fa-whatsapp text-sm"></i> Ingatkan WA
                        </a>`;
                    } else {
                        actionBtn = `<span class="text-slate-400 text-[10px]">No WA Kosong</span>`;
                    }
                }

                let sholatBadge = '-';
                if (reported) {
                    if (item.is_sholat_5) {
                        sholatBadge = `<span class="px-2 py-0.5 bg-emerald-50 text-emerald-700 font-bold rounded text-[10px] border border-emerald-200"><i class="fa-solid fa-check mr-0.5"></i>${item.sholat}</span>`;
                    } else {
                        sholatBadge = `<span class="px-2 py-0.5 bg-amber-50 text-amber-700 font-medium rounded text-[10px] border border-amber-200">${item.sholat}</span>`;
                    }
                }

                let tilawahBadge = '-';
                if (reported && item.tilawah && item.tilawah !== '-') {
                    tilawahBadge = `<span class="text-slate-800 font-medium font-serif italic"><i class="fa-solid fa-book-open text-teal-600 mr-1"></i>${item.tilawah}</span>`;
                }

                let dzikirBadge = '-';
                if (reported && item.dzikir && item.dzikir !== '-') {
                    dzikirBadge = `<span class="px-2 py-0.5 bg-sky-50 text-sky-700 font-medium rounded text-[10px] border border-sky-200">${item.dzikir}</span>`;
                }

                const waPhone = p.phone ? `<a href="https://wa.me/${p.phone}" target="_blank" class="text-emerald-700 font-mono font-medium hover:underline inline-flex items-center gap-1"><i class="fa-brands fa-whatsapp text-emerald-600"></i>+${p.phone}</a>` : '<span class="text-slate-400 font-mono">-</span>';

                html += `
                <tr class="hover:bg-slate-50/80 transition ${!reported ? 'bg-rose-50/20' : ''}">
                    <td class="py-3 px-3 text-center text-slate-400 font-mono">${idx + 1}</td>
                    <td class="py-3 px-3">
                        <span class="font-bold text-slate-800 text-sm block">${p.name}</span>
                    </td>
                    <td class="py-3 px-3">
                        <span class="px-1.5 py-0.5 rounded text-[10px] font-bold ${p.unit === 'OB' ? 'bg-amber-100 text-amber-800' : (p.unit === 'GARDENER' ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-800')}">${p.unit}</span>
                        <span class="text-[10px] text-slate-500 block mt-0.5">${p.job_title || ''}</span>
                    </td>
                    <td class="py-3 px-3">${waPhone}</td>
                    <td class="py-3 px-3 text-center">${statusBadge}</td>
                    <td class="py-3 px-3 font-mono text-[11px] text-slate-600">${item.report_time}</td>
                    <td class="py-3 px-3">${sholatBadge}</td>
                    <td class="py-3 px-3">${tilawahBadge}</td>
                    <td class="py-3 px-3">${dzikirBadge}</td>
                    <td class="py-3 px-3 text-center">${actionBtn}</td>
                </tr>`;
            });

            tbody.innerHTML = html;
        })
        .catch(err => {
            tbody.innerHTML = `<tr><td colspan="10" class="text-center py-8 text-rose-500 font-semibold">Gagal memuat radar: ${err.message}</td></tr>`;
        });
}

// -------------------------------------------------------------------------
// 2. RIWAYAT LOG TRANSAKSI MUTABA'AH LENGKAP
// -------------------------------------------------------------------------
function setMutabaahLogPreset(preset) {
    const today = new Date();
    const y = today.getFullYear();
    const m = String(today.getMonth() + 1).padStart(2, '0');
    const d = String(today.getDate()).padStart(2, '0');
    const todayStr = `${y}-${m}-${d}`;

    const startInput = document.getElementById('mutabaah-log-start');
    const endInput = document.getElementById('mutabaah-log-end');

    if (preset === 'today') {
        startInput.value = todayStr;
        endInput.value = todayStr;
    } else if (preset === 'yesterday') {
        const yest = new Date(today);
        yest.setDate(yest.getDate() - 1);
        const yD = yest.getFullYear();
        const mD = String(yest.getMonth() + 1).padStart(2, '0');
        const dD = String(yest.getDate()).padStart(2, '0');
        startInput.value = `${yD}-${mD}-${dD}`;
        endInput.value = `${yD}-${mD}-${dD}`;
    } else if (preset === '7days') {
        const p7 = new Date(today);
        p7.setDate(p7.getDate() - 6);
        const yD = p7.getFullYear();
        const mD = String(p7.getMonth() + 1).padStart(2, '0');
        const dD = String(p7.getDate()).padStart(2, '0');
        startInput.value = `${yD}-${mD}-${dD}`;
        endInput.value = todayStr;
    } else if (preset === 'month') {
        startInput.value = `${y}-${m}-01`;
        endInput.value = todayStr;
    } else if (preset === 'all') {
        startInput.value = '2026-08-01';
        endInput.value = todayStr;
    }

    loadMutabaahLogs();
}

function loadMutabaahLogsDebounced() {
    clearTimeout(mutabaahSearchTimer);
    mutabaahSearchTimer = setTimeout(loadMutabaahLogs, 300);
}

function loadMutabaahLogs() {
    const tbody = document.getElementById('mutabaah-logs-tbody');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="7" class="text-center py-8 text-slate-400"><i class="fa-solid fa-spinner fa-spin mr-2"></i>Memuat riwayat log...</td></tr>';

    const start = document.getElementById('mutabaah-log-start').value;
    const end = document.getElementById('mutabaah-log-end').value;
    const unit = document.getElementById('filter-mutabaah-unit').value;
    const search = document.getElementById('mutabaah-log-search').value;

    const url = `/api/ops/mutabaah/logs?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}&unit=${encodeURIComponent(unit)}&q=${encodeURIComponent(search)}`;

    fetch(url)
        .then(r => r.json())
        .then(data => {
            if (!data.success) throw new Error(data.error || 'Gagal memuat log');

            const counter = document.getElementById('mutabaah-logs-counter');
            if (counter) {
                counter.innerText = `Menampilkan ${data.total_records} catatan mutaba'ah`;
            }

            if (!data.logs || data.logs.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" class="text-center py-8 text-slate-400">Tidak ada log mutabaah yang cocok dengan filter ini.</td></tr>';
                return;
            }

            let html = '';
            data.logs.forEach((l, idx) => {
                const safeRaw = encodeURIComponent(l.raw_text || '');
                html += `
                <tr class="hover:bg-slate-50 transition">
                    <td class="py-3 px-3 font-mono text-[11px] text-slate-600">
                        <span class="font-bold text-slate-800 block">${l.date}</span>
                        <span>${l.time_wib ? l.time_wib + ' WIB' : '-'}</span>
                    </td>
                    <td class="py-3 px-3 font-bold text-slate-800">${l.nama}</td>
                    <td class="py-3 px-3">
                        <span class="px-1.5 py-0.5 bg-slate-100 rounded text-[10px] font-semibold text-slate-700">${l.unit}</span>
                    </td>
                    <td class="py-3 px-3 text-slate-700">${l.sholat || '-'}</td>
                    <td class="py-3 px-3 text-slate-800 font-serif italic">${l.tilawah || '-'}</td>
                    <td class="py-3 px-3 text-slate-700">${l.dzikir || '-'}</td>
                    <td class="py-3 px-3 text-center">
                        <button onclick="showMutabaahRawText('${l.nama}', '${l.date}', decodeURIComponent('${safeRaw}'))" class="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-[10px] font-semibold cursor-pointer">
                            <i class="fa-regular fa-message text-teal-600"></i> Detail
                        </button>
                    </td>
                </tr>`;
            });

            tbody.innerHTML = html;
        })
        .catch(err => {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center py-8 text-rose-500 font-semibold">Gagal memuat log: ${err.message}</td></tr>`;
        });
}

// -------------------------------------------------------------------------
// 3. RAPOR & EVALUASI KEDISIPLINAN TIM
// -------------------------------------------------------------------------
function loadMutabaahEvaluasi() {
    const tbody = document.getElementById('mutabaah-eval-tbody');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="10" class="text-center py-8 text-slate-400"><i class="fa-solid fa-spinner fa-spin mr-2"></i>Menghitung rapor kedisiplinan tim...</td></tr>';

    const start = document.getElementById('mutabaah-eval-start').value;
    const end = document.getElementById('mutabaah-eval-end').value;
    const unit = document.getElementById('filter-mutabaah-unit').value;

    const url = `/api/ops/mutabaah/evaluasi?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}&unit=${encodeURIComponent(unit)}`;

    fetch(url)
        .then(r => r.json())
        .then(data => {
            if (!data.success) throw new Error(data.error || 'Gagal memuat evaluasi');

            const totalDaysEl = document.getElementById('eval-total-days');
            if (totalDaysEl) totalDaysEl.innerText = `${data.total_days} Hari Kalender`;

            if (!data.evaluasi || data.evaluasi.length === 0) {
                tbody.innerHTML = '<tr><td colspan="10" class="text-center py-8 text-slate-400">Tidak ada personil terdaftar untuk filter ini.</td></tr>';
                return;
            }

            let html = '';
            data.evaluasi.forEach((e, idx) => {
                const p = e.personnel;
                const pct = e.compliance_pct;

                let badgeColor = 'emerald';
                let progressBg = 'bg-emerald-500';
                if (pct >= 85) {
                    badgeColor = 'emerald';
                    progressBg = 'bg-emerald-500';
                } else if (pct >= 70) {
                    badgeColor = 'sky';
                    progressBg = 'bg-sky-500';
                } else if (pct >= 50) {
                    badgeColor = 'amber';
                    progressBg = 'bg-amber-500';
                } else {
                    badgeColor = 'rose';
                    progressBg = 'bg-rose-500';
                }

                html += `
                <tr class="hover:bg-slate-50 transition">
                    <td class="py-3 px-3 text-center font-mono font-bold text-slate-500">${idx + 1}</td>
                    <td class="py-3 px-3">
                        <span class="font-bold text-slate-800 text-sm block">${p.name}</span>
                        ${p.phone ? `<a href="https://wa.me/${p.phone}" target="_blank" class="text-[10px] text-emerald-700 font-mono hover:underline">+${p.phone}</a>` : ''}
                    </td>
                    <td class="py-3 px-3">
                        <span class="px-1.5 py-0.5 rounded text-[10px] font-bold ${p.unit === 'OB' ? 'bg-amber-100 text-amber-800' : 'bg-slate-100 text-slate-800'}">${p.unit}</span>
                        <span class="text-[10px] text-slate-500 block mt-0.5">${p.job_title || ''}</span>
                    </td>
                    <td class="py-3 px-3 text-center font-bold text-slate-800 text-sm">
                        ${e.days_reported} <small class="text-slate-400 text-[10px]">/ ${e.total_days} hari</small>
                    </td>
                    <td class="py-3 px-3">
                        <div class="flex items-center justify-between gap-2 mb-1">
                            <span class="font-bold text-xs ${badgeColor === 'emerald' ? 'text-emerald-700' : (badgeColor === 'rose' ? 'text-rose-600' : 'text-slate-700')}">${pct}%</span>
                            <span class="text-[10px] text-slate-400">${e.days_reported} lapor</span>
                        </div>
                        <div class="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                            <div class="${progressBg} h-2 rounded-full transition-all duration-500" style="width: ${Math.min(100, pct)}%"></div>
                        </div>
                    </td>
                    <td class="py-3 px-3 text-center font-mono font-bold text-teal-700">${e.sholat_5_count}x</td>
                    <td class="py-3 px-3 text-center font-mono font-bold text-indigo-700">${e.tilawah_count}x</td>
                    <td class="py-3 px-3 text-center font-mono font-bold text-sky-700">${e.dzikir_count}x</td>
                    <td class="py-3 px-3 text-center">
                        <span class="px-2.5 py-1 rounded-full text-[10px] font-bold tracking-wide uppercase bg-${badgeColor}-100 text-${badgeColor}-800 border border-${badgeColor}-200">
                            ${e.predikat}
                        </span>
                    </td>
                    <td class="py-3 px-3 text-center font-mono text-[11px] text-slate-500">${e.last_reported_date}</td>
                </tr>`;
            });

            tbody.innerHTML = html;
        })
        .catch(err => {
            tbody.innerHTML = `<tr><td colspan="10" class="text-center py-8 text-rose-500 font-semibold">Gagal memuat evaluasi: ${err.message}</td></tr>`;
        });
}

// -------------------------------------------------------------------------
// 4. EKSPOR EXCEL & MODAL HELPERS
// -------------------------------------------------------------------------
function exportMutabaahExcel() {
    const unit = document.getElementById('filter-mutabaah-unit') ? document.getElementById('filter-mutabaah-unit').value : 'OB';
    let start = '';
    let end = '';

    if (currentMutabaahSubView === 'evaluasi') {
        start = document.getElementById('mutabaah-eval-start') ? document.getElementById('mutabaah-eval-start').value : '';
        end = document.getElementById('mutabaah-eval-end') ? document.getElementById('mutabaah-eval-end').value : '';
    } else {
        start = document.getElementById('mutabaah-log-start') ? document.getElementById('mutabaah-log-start').value : '';
        end = document.getElementById('mutabaah-log-end') ? document.getElementById('mutabaah-log-end').value : '';
    }

    const url = `/export/mutabaah/excel?unit=${encodeURIComponent(unit)}&start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}`;
    window.open(url, '_blank');
}

function openModalMutabaahGuide() {
    document.getElementById('modal-mutabaah-guide').classList.remove('hidden');
}

function closeModalMutabaahGuide() {
    document.getElementById('modal-mutabaah-guide').classList.add('hidden');
}

function showMutabaahRawText(nama, date, rawText) {
    document.getElementById('modal-detail-petugas-name').innerText = `Laporan Mutaba'ah: ${nama}`;
    document.getElementById('modal-detail-date').innerText = date;
    document.getElementById('modal-detail-raw-text').innerText = rawText || '(Teks pesan kosong)';
    document.getElementById('modal-mutabaah-detail').classList.remove('hidden');
}

function closeModalMutabaahDetail() {
    document.getElementById('modal-mutabaah-detail').classList.add('hidden');
}

// Hook ke global document ready
document.addEventListener('DOMContentLoaded', function() {
    // Inisialisasi jika tab mutabaah aktif secara default
    const urlParams = new URLSearchParams(window.location.search);
    const hash = window.location.hash;
    if (urlParams.get('tab') === 'tab-mutabaah' || hash === '#tab-mutabaah') {
        initMutabaahTab();
    }
});
</script>
"""
