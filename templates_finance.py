# -*- coding: utf-8 -*-
"""
templates_finance.py - Komponen Tampilan HTML & JavaScript untuk Tab Keuangan & FKP GA
An Nahl Islamic School - Dashboard Operasional note-umum
Mendukung Fitur View, Edit Koreksi, Hapus, Filter Tanggal Dinamis,
4 Grafik Analitik Keuangan (Chart.js), AI Financial Analyst Briefing, dan Ekspor Excel.
"""

TAB_KEUANGAN_HTML = """
<!-- TAB KEUANGAN & FKP GA AN NAHL -->
<div id="tab-keuangan" class="tab-content hidden space-y-6">

    <!-- 1. Header & Action Bar -->
    <div class="bg-white rounded-2xl shadow-xs border border-slate-200/80 p-4 sm:p-6 space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
            <div>
                <div class="flex items-center gap-2 flex-wrap">
                    <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 tracking-wider uppercase">Standar FKP GA 2026–2027</span>
                    <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-blue-100 text-blue-700">Vision AI & Google Drive</span>
                    <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-100 text-purple-800">Executive Financial Analytics</span>
                </div>
                <h2 class="text-base sm:text-xl font-bold text-slate-800 flex items-center gap-2 mt-1">
                    <i class="fa-solid fa-file-invoice-dollar text-emerald-600"></i>
                    Buku Kas & Pengeluaran Bagian Umum (General Affairs)
                </h2>
                <p class="text-xs text-slate-500 mt-0.5">Pencatatan otomatis bukti transfer m-banking & nota belanja via WhatsApp Bot Bu Rinni & Mr Slam, terintegrasi arsip Google Drive, analitik visual Chart.js, dan kontrol plafon anggaran FKP.</p>
            </div>
            <div class="flex items-center gap-2 sm:gap-3 flex-wrap">
                <button type="button" onclick="loadKeuanganGA()" class="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl transition flex items-center gap-1.5 cursor-pointer">
                    <i class="fa-solid fa-arrows-rotate"></i>
                    <span>Refresh</span>
                </button>
                <a href="https://wa.me/6285139373029" target="_blank" class="inline-flex items-center gap-1.5 px-3 py-2 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-200 rounded-xl text-xs font-semibold transition cursor-pointer shadow-2xs" title="Buka Chat WhatsApp Bot An Nahl Ops">
                    <i class="fa-brands fa-whatsapp text-emerald-600 text-sm"></i>
                    <span>Japri Bot: 0851-3937-3029</span>
                </a>
                <button type="button" onclick="exportGAExcel()" class="px-3.5 py-2 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-200 text-xs font-semibold rounded-xl transition flex items-center gap-1.5 cursor-pointer shadow-2xs" title="Unduh Laporan Keuangan GA Format Microsoft Excel (.xlsx)">
                    <i class="fa-solid fa-file-excel text-emerald-600"></i>
                    <span>Ekspor Excel (.xlsx)</span>
                </button>
            </div>
        </div>
    </div>

    <!-- 2. KONTROL FILTER PERIODE GLOBAL (DI ATAS CARD METRIK) -->
    <div class="bg-white rounded-2xl shadow-xs border border-slate-200/80 p-4 sm:p-5">
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-3">
            <div class="flex items-center gap-2.5">
                <div class="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center text-sm border border-emerald-200/60 shrink-0">
                    <i class="fa-solid fa-calendar-days"></i>
                </div>
                <div>
                    <h3 class="text-xs font-bold text-slate-800 uppercase tracking-wider">Periode Analisis Keuangan GA</h3>
                    <p class="text-[11px] text-slate-400 mt-0.5">Ubah rentang tanggal atau gunakan shortcut untuk menggerakkan kartu metrik dan grafik analitik.</p>
                </div>
            </div>

            <!-- Date Range Picker & Shortcuts -->
            <div class="flex items-center gap-2 flex-wrap">
                <div class="flex items-center bg-slate-50 border border-slate-200 rounded-xl px-2.5 py-1.5 gap-2 shadow-2xs">
                    <div class="flex items-center gap-1 text-slate-500 text-xs font-medium">
                        <i class="fa-regular fa-calendar text-emerald-600 text-xs"></i>
                        <span>Dari:</span>
                    </div>
                    <input type="date" id="filter-ga-start-date" onchange="onGADateChange()" class="bg-transparent text-slate-700 text-xs font-medium focus:outline-hidden cursor-pointer" title="Tanggal Mulai">
                    <span class="text-slate-300">|</span>
                    <div class="flex items-center gap-1 text-slate-500 text-xs font-medium">
                        <span>S/d:</span>
                    </div>
                    <input type="date" id="filter-ga-end-date" onchange="onGADateChange()" class="bg-transparent text-slate-700 text-xs font-medium focus:outline-hidden cursor-pointer" title="Tanggal Selesai">
                    <button type="button" onclick="resetGADateFilter()" class="text-slate-400 hover:text-rose-500 text-xs px-1 cursor-pointer transition" title="Hapus Filter Tanggal">
                        <i class="fa-solid fa-xmark"></i>
                    </button>
                </div>

                <!-- Shortcut Tanggal Cepat -->
                <div class="inline-flex items-center bg-slate-100/80 p-0.5 rounded-xl text-[11px] font-semibold text-slate-600">
                    <button type="button" onclick="setGADateShortcut('today')" class="px-2.5 py-1.5 rounded-lg hover:bg-white hover:text-slate-800 transition cursor-pointer">Hari Ini</button>
                    <button type="button" onclick="setGADateShortcut('7days')" class="px-2.5 py-1.5 rounded-lg hover:bg-white hover:text-slate-800 transition cursor-pointer">7 Hari</button>
                    <button type="button" onclick="setGADateShortcut('this_month')" class="px-2.5 py-1.5 rounded-lg hover:bg-white hover:text-slate-800 transition cursor-pointer">Bulan Ini</button>
                    <button type="button" onclick="setGADateShortcut('all')" class="px-2.5 py-1.5 rounded-lg bg-white text-emerald-700 font-bold shadow-2xs transition cursor-pointer">Semua</button>
                </div>
            </div>
        </div>
    </div>

    <!-- 3. 4 KARTU METRIK DINAMIS (UPDATE REAL-TIME SESUAI FILTER DI ATAS) -->
    <div class="space-y-2">
        <div class="flex items-center justify-between text-xs text-slate-500 pt-1 px-1">
            <div class="flex items-center gap-2">
                <span class="font-bold text-slate-700">Ringkasan Anggaran & Realisasi GA</span>
                <span id="ga-period-badge" class="text-[10px] px-2.5 py-0.5 rounded-full font-bold bg-emerald-100 text-emerald-800">Semua Periode Kumulatif</span>
            </div>
            <span class="text-[11px] text-slate-400">Terhitung otomatis sesuai tanggal/kategori aktif</span>
        </div>

        <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
            <!-- 1. Realisasi Belanja GA -->
            <div class="bg-rose-50/50 border border-rose-200/70 rounded-xl p-3.5 shadow-2xs">
                <div class="flex items-center justify-between text-rose-800 text-xs font-semibold">
                    <span>Realisasi Belanja GA</span>
                    <i class="fa-solid fa-money-bill-wave text-rose-500"></i>
                </div>
                <div id="ga-stat-grand-total" class="text-lg sm:text-2xl font-black text-rose-900 mt-1">Rp 0</div>
                <div id="ga-stat-total-trx-count" class="text-[11px] text-rose-700 font-medium mt-0.5">0 Transaksi Belanja</div>
            </div>

            <!-- 2. Bukti Transaksi Terverifikasi -->
            <div class="bg-blue-50/50 border border-blue-200/70 rounded-xl p-3.5 shadow-2xs">
                <div class="flex items-center justify-between text-blue-800 text-xs font-semibold">
                    <span>Bukti Transaksi</span>
                    <i class="fa-solid fa-receipt text-blue-500"></i>
                </div>
                <div id="ga-stat-total-trx" class="text-lg sm:text-2xl font-black text-blue-900 mt-1">0 Transaksi</div>
                <div class="text-[11px] text-blue-700 font-medium mt-0.5">Nota & transfer terurai Vision AI</div>
            </div>

            <!-- 3. Plafon RKAS GA & Serapan -->
            <div class="bg-purple-50/50 border border-purple-200/70 rounded-xl p-3.5 shadow-2xs">
                <div class="flex items-center justify-between text-purple-800 text-xs font-semibold">
                    <span>Plafon RKAS GA</span>
                    <i class="fa-solid fa-chart-pie text-purple-500"></i>
                </div>
                <div class="text-lg sm:text-2xl font-black text-purple-900 mt-1">Rp 1.507.851.796</div>
                <div id="ga-stat-pct-serapan" class="text-[11px] text-purple-700 font-bold mt-0.5">Serapan 0.0% dari Plafon</div>
            </div>

            <!-- 4. Sisa Plafon Anggaran GA -->
            <div class="bg-emerald-50/50 border border-emerald-200/70 rounded-xl p-3.5 shadow-2xs">
                <div class="flex items-center justify-between text-emerald-800 text-xs font-semibold">
                    <span>Sisa Plafon Anggaran</span>
                    <i class="fa-solid fa-vault text-emerald-600"></i>
                </div>
                <div id="ga-stat-sisa-budget" class="text-lg sm:text-2xl font-black text-emerald-900 mt-1">Rp 1.507.851.796</div>
                <div class="text-[11px] text-emerald-700 font-medium mt-0.5">Google Drive Safe (Disk: 0 Byte)</div>
            </div>
        </div>
    </div>

    <!-- 4. CARD ANALIS KEUANGAN AIS UNTUK GA (AI FINANCIAL ANALYST EXECUTIVE INSIGHTS) -->
    <div class="bg-white rounded-2xl shadow-xs border border-emerald-200/80 p-4 sm:p-5 space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3.5">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600 shadow-2xs shrink-0">
                    <i class="fa-solid fa-brain-circuit text-lg"></i>
                </div>
                <div>
                    <h3 class="text-sm sm:text-base font-bold text-slate-900 flex items-center gap-2">
                        Diagnosa & Analisis Keuangan Bagian Umum (Ais GA Intelligence)
                    </h3>
                    <p class="text-xs text-slate-500 font-medium mt-0.5">Evaluasi realisasi anggaran FKP GA, ritme belanja bulanan, dan audit efisiensi pengeluaran.</p>
                </div>
            </div>
            <div class="flex items-center gap-2 self-start sm:self-auto">
                <span class="text-xs font-semibold text-slate-500">Status Anggaran:</span>
                <span id="ai-ga-status-badge" class="px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-1.5 shadow-2xs">
                    <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                    <span id="ai-ga-status-text">ANGGARAN TERKENDALI</span>
                </span>
            </div>
        </div>

        <!-- 4 Mini Financial Ratios Cards -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div class="bg-emerald-50/60 rounded-xl p-3.5 border border-emerald-200/70">
                <div class="text-[11px] font-bold text-emerald-800 uppercase tracking-wider">Serapan Plafon Tahunan</div>
                <div id="ai-ga-serapan-pct" class="text-xl sm:text-2xl font-black text-emerald-900 mt-1">1.0%</div>
                <div class="text-[11px] text-emerald-700 font-medium mt-0.5">Dari total plafon Rp 1.5 Milyar</div>
            </div>
            <div class="bg-blue-50/60 rounded-xl p-3.5 border border-blue-200/70">
                <div class="text-[11px] font-bold text-blue-800 uppercase tracking-wider">Pos Serapan Terbesar</div>
                <div id="ai-ga-top-cost" class="text-xs sm:text-sm font-extrabold text-slate-900 truncate mt-1.5" title="Pemeliharaan & Perbaikan">PEMELIHARAAN (6.1%)</div>
                <div class="text-[11px] text-blue-700 font-semibold mt-0.5 truncate">Pos 51411 (Plafon Rp 181.7M)</div>
            </div>
            <div class="bg-amber-50/60 rounded-xl p-3.5 border border-amber-200/70">
                <div class="text-[11px] font-bold text-amber-800 uppercase tracking-wider">Penerima Transaksi Terbesar</div>
                <div id="ai-ga-top-vendor" class="text-xs sm:text-sm font-extrabold text-amber-900 truncate mt-1.5" title="Memuat...">Memuat...</div>
                <div id="ai-ga-top-vendor-desc" class="text-[11px] text-amber-700 font-semibold mt-0.5 truncate" title="Memuat uraian...">Memuat...</div>
            </div>
            <div class="bg-purple-50/60 rounded-xl p-3.5 border border-purple-200/70">
                <div class="text-[11px] font-bold text-purple-800 uppercase tracking-wider">Arsip Bukti & Keamanan</div>
                <div class="text-xs sm:text-sm font-extrabold text-purple-900 truncate mt-1.5">100% Google Drive</div>
                <div class="text-[11px] text-purple-700 font-semibold mt-0.5 truncate">Folder: Keuangan_GA</div>
            </div>
        </div>

        <!-- Catatan Analis Ais Box -->
        <div class="bg-slate-50/90 rounded-xl p-4 border border-slate-200/80">
            <div class="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2.5 flex items-center gap-2">
                <i class="fa-solid fa-lightbulb text-amber-500"></i>
                <span>Catatan & Rekomendasi Analis Ais untuk Manajemen GA (Mr Slam & Bu Rinni):</span>
            </div>
            <ul id="ai-ga-insights-list" class="space-y-2 text-xs">
                <li class="flex items-start gap-2.5 text-slate-700 font-medium">
                    <i class="fa-solid fa-circle-check text-emerald-600 mt-0.5 shrink-0 text-sm"></i>
                    <span class="leading-relaxed">Memuat analisis eksekutif GA...</span>
                </li>
            </ul>
        </div>
    </div>

    <!-- 5. DASHBOARD GRAFIK ANALITIK KEUANGAN GA (CHART.JS) -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-5">
        <!-- GRAFIK 1: Tren Belanja Bulanan GA (7 Cols) -->
        <div class="lg:col-span-7 bg-white rounded-2xl shadow-xs border border-slate-200/80 p-4 sm:p-5 flex flex-col justify-between">
            <div>
                <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                    <div>
                        <h3 class="text-sm font-bold text-slate-800 flex items-center gap-2">
                            <i class="fa-solid fa-chart-line text-emerald-600"></i>
                            Tren Pengeluaran Belanja GA Bulanan (TA 2026/2027)
                        </h3>
                        <p class="text-[11px] text-slate-400 mt-0.5">Ritme realisasi pengeluaran bulanan bagian umum terintegrasi standar FKP.</p>
                    </div>
                    <span class="text-[10px] font-bold px-2 py-0.5 bg-emerald-50 text-emerald-700 rounded-md">Bulanan</span>
                </div>
                <div class="relative w-full h-64 sm:h-72 mt-3">
                    <canvas id="chartGATrends"></canvas>
                </div>
            </div>
            <div class="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
                <span>Rata-rata belanja berjalan terpantau aman terkendali.</span>
                <span class="font-bold text-emerald-700">TA 2026/2027</span>
            </div>
        </div>

        <!-- GRAFIK 2: Komposisi Pengeluaran 5 Pos Induk FKP GA (5 Cols) -->
        <div class="lg:col-span-5 bg-white rounded-2xl shadow-xs border border-slate-200/80 p-4 sm:p-5 flex flex-col justify-between">
            <div>
                <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                    <div>
                        <h3 class="text-sm font-bold text-slate-800 flex items-center gap-2">
                            <i class="fa-solid fa-chart-pie text-blue-600"></i>
                            Komposisi Belanja 5 Pos Induk FKP GA
                        </h3>
                        <p class="text-[11px] text-slate-400 mt-0.5">Proporsi pengeluaran berdasarkan kategori mata anggaran.</p>
                    </div>
                    <span class="text-[10px] font-bold px-2 py-0.5 bg-blue-50 text-blue-700 rounded-md">Distribusi Pos</span>
                </div>
                <div class="relative w-full h-64 sm:h-72 mt-3 flex items-center justify-center">
                    <canvas id="chartGAComposition"></canvas>
                </div>
            </div>
            <div class="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
                <span>Dominasi belanja: Pemeliharaan Sarpras & Investasi.</span>
                <span class="font-bold text-blue-700">5 Pos Utama</span>
            </div>
        </div>

        <!-- GRAFIK 3: Evaluasi Realisasi vs Plafon 5 Pos Induk FKP GA (6 Cols) -->
        <div class="lg:col-span-6 bg-white rounded-2xl shadow-xs border border-slate-200/80 p-4 sm:p-5 flex flex-col justify-between">
            <div>
                <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                    <div>
                        <h3 class="text-sm font-bold text-slate-800 flex items-center gap-2">
                            <i class="fa-solid fa-scale-balanced text-purple-600"></i>
                            Realisasi vs Plafon 5 Pos Induk FKP GA (Rp 1.5 M)
                        </h3>
                        <p class="text-[11px] text-slate-400 mt-0.5">Monitoring serapan belanja operasional terhadap batas pagu tahunan.</p>
                    </div>
                    <span class="text-[10px] font-bold px-2 py-0.5 bg-purple-50 text-purple-700 rounded-md">Plafon vs Realisasi</span>
                </div>
                <div class="relative w-full h-64 sm:h-72 mt-3">
                    <canvas id="chartGABudget"></canvas>
                </div>
            </div>
            <div class="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
                <span>Plafon RKAS GA: Rp 1.507.851.796</span>
                <span class="font-bold text-purple-700">Kontrol Pagu</span>
            </div>
        </div>

        <!-- GRAFIK 4: Top Item Pengeluaran Operasional GA Terbesar (6 Cols) -->
        <div class="lg:col-span-6 bg-white rounded-2xl shadow-xs border border-slate-200/80 p-4 sm:p-5 flex flex-col justify-between">
            <div>
                <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                    <div>
                        <h3 class="text-sm font-bold text-slate-800 flex items-center gap-2">
                            <i class="fa-solid fa-ranking-star text-amber-500"></i>
                            Top Item Beban Pengeluaran GA Terbesar
                        </h3>
                        <p class="text-[11px] text-slate-400 mt-0.5">Item belanja dan pengeluaran dengan nilai transaksi tertinggi.</p>
                    </div>
                    <span class="text-[10px] font-bold px-2 py-0.5 bg-amber-50 text-amber-700 rounded-md">Top Expenses</span>
                </div>
                <div class="relative w-full h-64 sm:h-72 mt-3">
                    <canvas id="chartGATopExp"></canvas>
                </div>
            </div>
            <div class="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
                <span>Item belanja modal & renovasi sarpras sekolah.</span>
                <span class="font-bold text-amber-700">Audit Detail</span>
            </div>
        </div>
    </div>

    <!-- 6. KONTROL 5 POS PLAFON ANGGARAN FKP GA (MINI BARS) -->
    <div class="bg-white rounded-2xl shadow-xs border border-slate-200/80 p-4 sm:p-6 space-y-4">
        <h3 class="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2">
            <i class="fa-solid fa-layer-group text-slate-400"></i>
            Detail Kontrol 5 Pos Plafon Anggaran FKP GA 2026–2027
        </h3>
        <div id="finance-categories-container" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
            <div class="text-center py-4 text-xs text-slate-400 col-span-full">Memuat data alokasi anggaran...</div>
        </div>
    </div>

    <!-- 7. DATA TABLE TRANSAKSI PENGELUARAN GA -->
    <div class="bg-white rounded-2xl shadow-xs border border-slate-200/80 overflow-hidden">
        <!-- Sub-Header Title & Live Stats -->
        <div class="p-4 sm:p-5 border-b border-slate-100 flex flex-col md:flex-row md:items-center justify-between gap-3">
            <div>
                <h3 class="text-sm font-bold text-slate-800 flex items-center gap-2">
                    <i class="fa-solid fa-table-list text-emerald-600"></i>
                    <span>Tabel Rincian Pengeluaran Bagian Umum (GA)</span>
                </h3>
                <p class="text-xs text-slate-500 mt-0.5">
                    Menampilkan <span id="ga-table-count" class="font-bold text-emerald-700">0</span> transaksi aktif | Total Belanja: <span id="ga-table-total-amount" class="font-bold text-rose-700">Rp 0</span>
                </p>
            </div>
            <!-- Quick Table Search & Reset -->
            <div class="flex items-center gap-2 flex-wrap">
                <div class="relative w-full sm:w-64">
                    <input type="text" id="ga-table-quick-search" oninput="onGATableFilterChange()" placeholder="Cari uraian, toko, no KB..." class="w-full pl-9 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-700 focus:ring-2 focus:ring-emerald-500 focus:outline-hidden">
                    <i class="fa-solid fa-magnifying-glass absolute left-3 top-2.5 text-slate-400 text-xs"></i>
                </div>
                <button type="button" onclick="resetGATableFilters()" class="px-2.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-xl text-xs font-semibold transition cursor-pointer flex items-center gap-1" title="Reset Filter Tabel">
                    <i class="fa-solid fa-rotate-left"></i>
                    <span>Reset</span>
                </button>
            </div>
        </div>

        <!-- In-Table Multi-Filter Bar -->
        <div class="bg-slate-50/70 p-3 sm:px-5 border-b border-slate-200/70 flex flex-wrap items-center justify-between gap-2.5 text-xs">
            <div class="flex flex-wrap items-center gap-2">
                <!-- Filter Unit Target -->
                <div class="flex items-center gap-1">
                    <span class="text-[11px] font-semibold text-slate-500">Unit:</span>
                    <select id="ga-table-filter-unit" onchange="onGATableFilterChange()" class="px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-medium text-slate-700 focus:outline-hidden">
                        <option value="">Semua Unit</option>
                        <option value="SD">SD</option>
                        <option value="SMP">SMP</option>
                        <option value="SMA">SMA</option>
                        <option value="TK">TK / PGTK</option>
                        <option value="GA">GA / Umum</option>
                        <option value="Kolam Renang">Kolam Renang</option>
                        <option value="Futsal">Lapangan Futsal</option>
                        <option value="Masjid">Masjid</option>
                    </select>
                </div>

                <!-- Filter Pos Induk FKP GA -->
                <div class="flex items-center gap-1">
                    <span class="text-[11px] font-semibold text-slate-500">Pos:</span>
                    <select id="ga-table-filter-cat" onchange="onGATableFilterChange()" class="px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-medium text-slate-700 focus:outline-hidden">
                        <option value="">Semua Pos (5 Induk FKP)</option>
                        <option value="PEMELIHARAAN">51411 Pemeliharaan</option>
                        <option value="ADMINISTRASI">51412 Administrasi</option>
                        <option value="ENERGI">51413 Listrik & Net</option>
                        <option value="PERLENGKAPAN">51414 Perlengkapan</option>
                        <option value="INVESTASI">51415 Investasi Sarpras</option>
                    </select>
                </div>

                <!-- Filter Nominal -->
                <div class="flex items-center gap-1">
                    <span class="text-[11px] font-semibold text-slate-500">Nominal:</span>
                    <select id="ga-table-filter-nominal" onchange="onGATableFilterChange()" class="px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-medium text-slate-700 focus:outline-hidden">
                        <option value="">Semua Nominal</option>
                        <option value="gt_10m">> Rp 10 Juta (Proyek Besar)</option>
                        <option value="1m_10m">Rp 1 Juta s/d 10 Juta</option>
                        <option value="lt_1m">< Rp 1 Juta (Operasional Kecil)</option>
                    </select>
                </div>

                <!-- Filter Bukti Nota -->
                <div class="flex items-center gap-1">
                    <span class="text-[11px] font-semibold text-slate-500">Bukti:</span>
                    <select id="ga-table-filter-proof" onchange="onGATableFilterChange()" class="px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-medium text-slate-700 focus:outline-hidden">
                        <option value="">Semua</option>
                        <option value="with_proof">📸 Ada Bukti Drive</option>
                        <option value="no_proof">Tanpa Bukti</option>
                    </select>
                </div>
            </div>

            <!-- Sorting & Rows Per Page -->
            <div class="flex items-center gap-2">
                <div class="flex items-center gap-1">
                    <span class="text-[11px] font-semibold text-slate-500">Urutkan:</span>
                    <select id="ga-table-sort" onchange="onGATableFilterChange()" class="px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-medium text-slate-700 focus:outline-hidden">
                        <option value="date_desc">Tanggal Terbaru</option>
                        <option value="date_asc">Tanggal Terlama</option>
                        <option value="amount_desc">Nominal Terbesar</option>
                        <option value="amount_asc">Nominal Terkecil</option>
                    </select>
                </div>

                <div class="flex items-center gap-1">
                    <span class="text-[11px] font-semibold text-slate-500">Baris:</span>
                    <select id="ga-table-pagesize" onchange="onGAPageSizeChange()" class="px-2 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-medium text-slate-700 focus:outline-hidden">
                        <option value="25">25</option>
                        <option value="50">50</option>
                        <option value="100">100</option>
                        <option value="all">Semua</option>
                    </select>
                </div>
            </div>
        </div>

        <div class="overflow-x-auto">
            <table class="w-full text-left border-collapse text-xs min-w-[900px]">
                <thead>
                    <tr class="bg-slate-50/90 border-b border-slate-200 text-slate-600 font-bold uppercase tracking-wider text-[11px]">
                        <th class="py-3 px-4">Tanggal & No. KB</th>
                        <th class="py-3 px-4">Mata Anggaran (COA)</th>
                        <th class="py-3 px-4">Penerima / Toko</th>
                        <th class="py-3 px-4">Uraian Kebutuhan</th>
                        <th class="py-3 px-4 text-right">Nominal (Rp)</th>
                        <th class="py-3 px-4">Sumber / Unit</th>
                        <th class="py-3 px-4">Pelapor</th>
                        <th class="py-3 px-4 text-center">Bukti Nota</th>
                        <th class="py-3 px-4 text-center">Aksi / Koreksi</th>
                    </tr>
                </thead>
                <tbody id="finance-table-tbody" class="divide-y divide-slate-100 text-slate-700">
                    <tr>
                        <td colspan="9" class="py-8 text-center text-slate-400">
                            <i class="fa-solid fa-spinner fa-spin text-lg text-emerald-500 mb-2 block"></i>
                            Memuat riwayat pengeluaran GA...
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
        <div id="finance-empty-state" class="hidden py-12 text-center text-slate-400">
            <i class="fa-regular fa-folder-open text-4xl text-slate-300 mb-3 block"></i>
            <p class="font-medium text-slate-600">Belum ada pengeluaran yang cocok dengan filter tabel.</p>
            <p class="text-xs text-slate-400 mt-1">Gunakan tombol reset filter tabel untuk menampilkan seluruh transaksi.</p>
        </div>

        <!-- Table Pagination Footer -->
        <div id="ga-table-pagination" class="p-3.5 border-t border-slate-100 bg-slate-50/50 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-500">
            <div id="ga-pagination-info">Menampilkan 0 - 0 dari 0 transaksi</div>
            <div class="flex items-center gap-1" id="ga-pagination-buttons">
                <!-- Injected via JS -->
            </div>
        </div>
    </div>
</div>

<!-- MODAL DETAIL TRANSAKSI & BUKTI BAYAR -->
<div id="modal-finance-detail" class="fixed inset-0 bg-slate-900/60 backdrop-blur-xs z-50 hidden flex items-center justify-center p-4">
    <div class="bg-white rounded-2xl max-w-xl w-full p-6 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
        <div class="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 class="text-base font-bold text-slate-800 flex items-center gap-2">
                <i class="fa-solid fa-receipt text-emerald-600"></i>
                <span id="detail-exp-title">Detail Transaksi Pengeluaran GA</span>
            </h3>
            <button type="button" onclick="toggleModal('modal-finance-detail')" class="text-slate-400 hover:text-slate-600 cursor-pointer">
                <i class="fa-solid fa-xmark text-lg"></i>
            </button>
        </div>

        <div class="space-y-3 text-xs" id="detail-exp-body">
            <!-- Populated dynamically -->
        </div>

        <div class="border-t border-slate-100 pt-3 flex justify-end gap-2">
            <button type="button" onclick="toggleModal('modal-finance-detail')" class="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-xl text-xs transition cursor-pointer">Tutup</button>
        </div>
    </div>
</div>

<!-- MODAL EDIT / KOREKSI TRANSAKSI PENGELUARAN GA -->
<div id="modal-finance-edit" class="fixed inset-0 bg-slate-900/60 backdrop-blur-xs z-50 hidden flex items-center justify-center p-4">
    <div class="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
        <div class="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
                <h3 class="text-base font-bold text-slate-800 flex items-center gap-2">
                    <i class="fa-solid fa-pen-to-square text-amber-500"></i>
                    <span>Koreksi Transaksi Pengeluaran GA</span>
                </h3>
                <p class="text-xs text-slate-400 mt-0.5">Sesuaikan data transaksi, nominal, dan pos anggaran FKP bila hasil ekstraksi AI perlu disempurnakan.</p>
            </div>
            <button type="button" onclick="toggleModal('modal-finance-edit')" class="text-slate-400 hover:text-slate-600 cursor-pointer">
                <i class="fa-solid fa-xmark text-lg"></i>
            </button>
        </div>

        <form id="form-edit-expense" onsubmit="submitEditExpense(event)" class="space-y-4 text-xs">
            <input type="hidden" id="edit-exp-id">

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                    <label class="block font-bold text-slate-700 mb-1">Tanggal Transaksi</label>
                    <input type="date" id="edit-exp-date" required class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-hidden">
                </div>
                <div>
                    <label class="block font-bold text-slate-700 mb-1">Nominal (Rp)</label>
                    <input type="number" id="edit-exp-amount" required class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-hidden font-bold">
                </div>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                    <label class="block font-bold text-slate-700 mb-1">Penerima / Nama Toko</label>
                    <input type="text" id="edit-exp-vendor" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-hidden">
                </div>
                <div>
                    <label class="block font-bold text-slate-700 mb-1">Nomor Referensi / No Nota</label>
                    <input type="text" id="edit-exp-ref" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-hidden">
                </div>
            </div>

            <div>
                <label class="block font-bold text-slate-700 mb-1">Pos Mata Anggaran FKP GA</label>
                <select id="edit-exp-coa" required class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-hidden">
                    <option value="51411-001">51411-001 Pemeliharaan Gedung (PEMELIHARAAN)</option>
                    <option value="51411-002">51411-002 Obat Kolam Renang (PEMELIHARAAN)</option>
                    <option value="51411-003">51411-003 Treatment Kolam Renang (PEMELIHARAAN)</option>
                    <option value="51411-004">51411-004 Prasarana Jalan & Pagar (PEMELIHARAAN)</option>
                    <option value="51411-005">51411-005 Service Motor GA (PEMELIHARAAN)</option>
                    <option value="51411-006">51411-006 Service Mobil Sekolah (PEMELIHARAAN)</option>
                    <option value="51411-011">51411-011 Cuci AC Sekolah (PEMELIHARAAN)</option>
                    <option value="51411-012">51411-012 Perbaikan AC (PEMELIHARAAN)</option>
                    <option value="51412-002">51412-002 Iuran Lingkungan / Keamanan (ADMINISTRASI)</option>
                    <option value="51412-004">51412-004 Biaya Admin Bank (ADMINISTRASI)</option>
                    <option value="51412-006">51412-006 Petty Cash GA / Kas Kecil (ADMINISTRASI)</option>
                    <option value="51412-007">51412-007 Konsumsi Rapat & Lembur (ADMINISTRASI)</option>
                    <option value="51413-001">51413-001 Listrik PLN (ENERGI & KOMUNIKASI)</option>
                    <option value="51413-002">51413-002 Telepon & Internet (ENERGI & KOMUNIKASI)</option>
                    <option value="51413-003">51413-003 Air PDAM & Galon (ENERGI & KOMUNIKASI)</option>
                    <option value="51414-001">51414-001 Perlengkapan Kebersihan OB (PERLENGKAPAN)</option>
                    <option value="51414-002">51414-002 Perlengkapan Taman (PERLENGKAPAN)</option>
                    <option value="51414-003">51414-003 Bahan Habis Pakai Chemical (PERLENGKAPAN)</option>
                    <option value="51414-004">51414-004 Alat Kerja Sarpras (PERLENGKAPAN)</option>
                    <option value="51415-001">51415-001 Investasi PGTK (INVESTASI)</option>
                    <option value="51415-002">51415-002 Investasi SD (INVESTASI)</option>
                    <option value="51415-003">51415-003 Investasi SMP (INVESTASI)</option>
                    <option value="51415-004">51415-004 Investasi SMA (INVESTASI)</option>
                    <option value="51415-005">51415-005 Investasi Sarpras Umum (INVESTASI)</option>
                </select>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                    <label class="block font-bold text-slate-700 mb-1">Sumber Dana</label>
                    <select id="edit-exp-fund" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-hidden">
                        <option value="2. SPP">2. SPP</option>
                        <option value="1. APBS Unit">1. APBS Unit</option>
                    </select>
                </div>
                <div>
                    <label class="block font-bold text-slate-700 mb-1">Unit Target</label>
                    <select id="edit-exp-unit" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-hidden">
                        <option value="Umum">Umum</option>
                        <option value="SD">SD</option>
                        <option value="SMP">SMP</option>
                        <option value="SMA">SMA</option>
                        <option value="PGTK">PGTK</option>
                    </select>
                </div>
            </div>

            <div>
                <label class="block font-bold text-slate-700 mb-1">Uraian Kebutuhan / Keterangan</label>
                <textarea id="edit-exp-desc" rows="3" required class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-hidden"></textarea>
            </div>

            <div class="border-t border-slate-100 pt-3 flex items-center justify-between">
                <button type="button" onclick="deleteCurrentExpense()" class="px-3.5 py-2 bg-rose-50 hover:bg-rose-100 text-rose-700 font-semibold rounded-xl transition cursor-pointer">
                    <i class="fa-solid fa-trash mr-1"></i>
                    <span>Hapus Transaksi</span>
                </button>
                <div class="flex items-center gap-2">
                    <button type="button" onclick="toggleModal('modal-finance-edit')" class="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-xl transition cursor-pointer">Batal</button>
                    <button type="submit" id="btn-save-edit-expense" class="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-xl shadow-xs transition flex items-center gap-1.5 cursor-pointer">
                        <i class="fa-solid fa-check"></i>
                        <span>Simpan Perubahan</span>
                    </button>
                </div>
            </div>
        </form>
    </div>
</div>
"""

JS_KEUANGAN_SCRIPTS = """
<script>
    let G_FINANCE_DATA = [];

    function onGADateChange() {
        loadKeuanganGA();
    }

    function resetGADateFilter() {
        const s = document.getElementById('filter-ga-start-date');
        const e = document.getElementById('filter-ga-end-date');
        if (s) s.value = '';
        if (e) e.value = '';
        loadKeuanganGA();
    }

    function setGADateShortcut(type) {
        const s = document.getElementById('filter-ga-start-date');
        const e = document.getElementById('filter-ga-end-date');
        if (!s || !e) return;

        const now = new Date();
        const pad = (n) => String(n).padStart(2, '0');
        const formatYMD = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;

        if (type === 'today') {
            const todayStr = formatYMD(now);
            s.value = todayStr;
            e.value = todayStr;
        } else if (type === '7days') {
            const past = new Date(now.getTime() - (7 * 24 * 60 * 60 * 1000));
            s.value = formatYMD(past);
            e.value = formatYMD(now);
        } else if (type === 'this_month') {
            const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
            s.value = formatYMD(firstDay);
            e.value = formatYMD(now);
        } else if (type === 'all') {
            s.value = '';
            e.value = '';
        }
        loadKeuanganGA();
    }

    async function loadKeuanganGA() {
        try {
            const startDate = document.getElementById('filter-ga-start-date') ? document.getElementById('filter-ga-start-date').value : '';
            const endDate = document.getElementById('filter-ga-end-date') ? document.getElementById('filter-ga-end-date').value : '';

            let statsUrl = '/api/ga/expenses/stats?1=1';
            let expUrl = '/api/ga/expenses?1=1';

            if (startDate) {
                statsUrl += '&start_date=' + encodeURIComponent(startDate);
                expUrl += '&start_date=' + encodeURIComponent(startDate);
            }
            if (endDate) {
                statsUrl += '&end_date=' + encodeURIComponent(endDate);
                expUrl += '&end_date=' + encodeURIComponent(endDate);
            }

            // 1. Fetch Stats
            const resStats = await fetch(statsUrl);
            if (resStats.ok) {
                const sData = await resStats.json();
                if (sData.success) {
                    renderFinanceStats(sData);
                    renderGACharts(sData);
                }
            }

            // 2. Fetch Expenses Data
            const resExp = await fetch(expUrl);
            if (resExp.ok) {
                const eData = await resExp.json();
                if (eData.success) {
                    G_FINANCE_DATA = eData.data || [];
                    filterGAData();
                }
            }
        } catch (err) {
            console.error('Error loadKeuanganGA:', err);
        }
    }

    function renderFinanceStats(stats) {
        const grandTotal = stats.grand_total_realisasi || 0;
        const totalTrx = stats.total_transaksi || 0;
        const totalBudget = stats.grand_budget_annual || 1507851796;
        const pct = stats.overall_pct || (grandTotal / totalBudget * 100).toFixed(1);
        const sisa = stats.sisa_budget !== undefined ? stats.sisa_budget : (totalBudget - grandTotal);
        const ai = stats.ai_analysis || {};

        // Badge Periode
        const startDate = document.getElementById('filter-ga-start-date') ? document.getElementById('filter-ga-start-date').value : '';
        const endDate = document.getElementById('filter-ga-end-date') ? document.getElementById('filter-ga-end-date').value : '';
        const badgeEl = document.getElementById('ga-period-badge');

        let isFiltered = false;
        let periodLabel = 'Semua Periode Kumulatif';
        if (startDate && endDate) {
            periodLabel = (startDate === endDate) ? `Tanggal: ${startDate}` : `${startDate} s/d ${endDate}`;
            isFiltered = true;
        } else if (startDate) {
            periodLabel = `Mulai ${startDate}`;
            isFiltered = true;
        } else if (endDate) {
            periodLabel = `Hingga ${endDate}`;
            isFiltered = true;
        }

        if (badgeEl) {
            badgeEl.innerText = periodLabel;
            badgeEl.className = isFiltered
                ? 'text-[10px] px-2.5 py-0.5 rounded-full font-bold bg-amber-100 text-amber-800'
                : 'text-[10px] px-2.5 py-0.5 rounded-full font-bold bg-emerald-100 text-emerald-800';
        }

        // Summary Cards
        document.getElementById('ga-stat-grand-total').innerText = 'Rp ' + Math.round(grandTotal).toLocaleString('id-ID');
        document.getElementById('ga-stat-total-trx-count').innerText = isFiltered
            ? `${totalTrx} Transaksi Belanja (${periodLabel})`
            : `${totalTrx} Transaksi Belanja (Kumulatif)`;

        document.getElementById('ga-stat-total-trx').innerText = totalTrx + ' Transaksi';
        document.getElementById('ga-stat-pct-serapan').innerText = `Serapan ${pct}% dari Plafon`;
        document.getElementById('ga-stat-sisa-budget').innerText = 'Rp ' + Math.round(sisa).toLocaleString('id-ID');

        // AI Briefing
        const statusBadge = document.getElementById('ai-ga-status-badge');
        const statusText = document.getElementById('ai-ga-status-text');
        if (statusBadge && statusText) {
            statusText.innerText = ai.status || 'ANGGARAN TERKENDALI';
            statusBadge.className = 'px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-1.5 shadow-2xs';
        }

        if (document.getElementById('ai-ga-serapan-pct')) {
            document.getElementById('ai-ga-serapan-pct').innerText = (pct) + '%';
        }
        if (document.getElementById('ai-ga-top-cost')) {
            const costEl = document.getElementById('ai-ga-top-cost');
            costEl.innerText = ai.top_cost_center || 'PEMELIHARAAN (6.1%)';
            costEl.title = ai.top_cost_center || 'PEMELIHARAAN';
        }
        if (document.getElementById('ai-ga-top-vendor')) {
            const vendorEl = document.getElementById('ai-ga-top-vendor');
            vendorEl.innerText = ai.top_vendor || '-';
            vendorEl.title = ai.top_vendor || '-';
        }
        if (document.getElementById('ai-ga-top-vendor-desc')) {
            const vendorDescEl = document.getElementById('ai-ga-top-vendor-desc');
            vendorDescEl.innerText = ai.top_vendor_desc || 'Akumulasi transaksi vendor';
            vendorDescEl.title = ai.top_vendor_desc || '';
        }

        const insightsList = document.getElementById('ai-ga-insights-list');
        if (insightsList && ai.insights) {
            insightsList.innerHTML = ai.insights.map(txt => `
                <li class="flex items-start gap-2.5 text-xs text-slate-800 font-medium">
                    <i class="fa-solid fa-circle-check text-emerald-600 mt-0.5 shrink-0 text-sm"></i>
                    <span class="leading-relaxed">${txt}</span>
                </li>
            `).join('');
        }

        // Render 5 Kategori Bar
        const catContainer = document.getElementById('finance-categories-container');
        if (catContainer) {
            const catMap = {};
            (stats.categories || []).forEach(c => {
                catMap[c.category] = c;
            });

            const fixedCategories = [
                { code: '51411', name: 'Pemeliharaan & Perbaikan', cat: 'PEMELIHARAAN & PERBAIKAN', budget: 181724000 },
                { code: '51412', name: 'Administrasi & Umum / Kas', cat: 'ADMINISTRASI DAN UMUM', budget: 102350000 },
                { code: '51413', name: 'Energi & Komunikasi', cat: 'ENERGI & KOMUNIKASI', budget: 479250000 },
                { code: '51414', name: 'Perlengkapan & Sanitasi', cat: 'PERLENGKAPAN', budget: 86527796 },
                { code: '51415', name: 'Investasi Sarpras', cat: 'INVESTASI', budget: 658000000 }
            ];

            let html = '';
            fixedCategories.forEach(fc => {
                const row = catMap[fc.cat] || { realisasi: 0, sisa: fc.budget, persentase: 0 };
                const real = row.realisasi || 0;
                const bgt = fc.budget;
                const pctVal = (real / bgt * 100).toFixed(1);
                let barColor = 'bg-emerald-500';
                if (pctVal >= 100) barColor = 'bg-rose-500';
                else if (pctVal >= 80) barColor = 'bg-amber-500';

                html += `
                <div class="border border-slate-200/80 rounded-xl p-3 bg-slate-50/50 hover:bg-slate-50 transition">
                    <div class="text-[11px] font-bold text-slate-700 truncate" title="${fc.name}">${fc.code} ${fc.name}</div>
                    <div class="text-sm font-bold text-slate-800 mt-1">Rp ${Math.round(real).toLocaleString('id-ID')}</div>
                    <div class="w-full bg-slate-200 rounded-full h-1.5 mt-2 overflow-hidden">
                        <div class="${barColor} h-1.5 rounded-full" style="width: ${Math.min(pctVal, 100)}%"></div>
                    </div>
                    <div class="flex justify-between text-[10px] text-slate-400 mt-1">
                        <span>${pctVal}% terpakai</span>
                        <span>Plafon: ${(bgt / 1000000).toFixed(0)}M</span>
                    </div>
                </div>`;
            });
            catContainer.innerHTML = html;
        }
    }

    function renderGACharts(stats) {
        if (typeof Chart === 'undefined') return;

        // Cleanup instance sebelumnya agar tidak numpuk
        if (window.gaChartMonthly instanceof Chart) window.gaChartMonthly.destroy();
        if (window.gaChartComposition instanceof Chart) window.gaChartComposition.destroy();
        if (window.gaChartBudget instanceof Chart) window.gaChartBudget.destroy();
        if (window.gaChartTopExp instanceof Chart) window.gaChartTopExp.destroy();

        // 1. Chart Tren Belanja Bulanan
        const trends = stats.monthly_trends || [];
        const tLabels = trends.map(t => t.month);
        const tExp = trends.map(t => t.expense);

        const ctxMonthly = document.getElementById('chartGATrends');
        if (ctxMonthly) {
            window.gaChartMonthly = new Chart(ctxMonthly, {
                type: 'bar',
                data: {
                    labels: tLabels,
                    datasets: [{
                        label: 'Belanja GA (Rp)',
                        data: tExp,
                        backgroundColor: 'rgba(225, 29, 72, 0.75)',
                        borderColor: '#E11D48',
                        borderWidth: 1.5,
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'top', labels: { boxWidth: 12, font: { size: 11 } } },
                        tooltip: {
                            callbacks: {
                                label: (ctx) => 'Belanja: Rp ' + Math.round(ctx.parsed.y).toLocaleString('id-ID')
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: (v) => 'Rp ' + (v >= 1000000 ? (v/1000000).toFixed(1) + 'M' : (v/1000).toFixed(0) + 'K')
                            }
                        }
                    }
                }
            });
        }

        // 2. Chart Komposisi 5 Pos Induk FKP GA (Donut)
        const categories = stats.categories || [];
        const cLabels = categories.map(c => c.category);
        const cData = categories.map(c => c.realisasi);

        const ctxComp = document.getElementById('chartGAComposition');
        if (ctxComp) {
            window.gaChartComposition = new Chart(ctxComp, {
                type: 'doughnut',
                data: {
                    labels: cLabels,
                    datasets: [{
                        data: cData,
                        backgroundColor: [
                            'rgba(16, 185, 129, 0.85)',
                            'rgba(59, 130, 246, 0.85)',
                            'rgba(245, 158, 11, 0.85)',
                            'rgba(139, 92, 246, 0.85)',
                            'rgba(244, 63, 94, 0.85)'
                        ],
                        borderWidth: 2,
                        borderColor: '#FFFFFF'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 10 } } },
                        tooltip: {
                            callbacks: {
                                label: (ctx) => {
                                    const val = ctx.parsed || 0;
                                    const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                                    const pct = total > 0 ? ((val / total) * 100).toFixed(1) : '0.0';
                                    return `${ctx.label}: Rp ${Math.round(val).toLocaleString('id-ID')} (${pct}%)`;
                                }
                            }
                        }
                    },
                    cutout: '65%'
                }
            });
        }

        // 3. Chart Realisasi vs Plafon 5 Pos Induk FKP GA (Horizontal Bar)
        const ctxBudget = document.getElementById('chartGABudget');
        if (ctxBudget) {
            const bLabels = categories.map(c => c.category.length > 20 ? c.category.substring(0, 18) + '...' : c.category);
            const bPlafon = categories.map(c => c.anggaran);
            const bReal = categories.map(c => c.realisasi);

            window.gaChartBudget = new Chart(ctxBudget, {
                type: 'bar',
                data: {
                    labels: bLabels,
                    datasets: [
                        {
                            label: 'Plafon RKAS (Rp)',
                            data: bPlafon,
                            backgroundColor: 'rgba(203, 213, 225, 0.7)',
                            borderColor: '#94A3B8',
                            borderWidth: 1,
                            borderRadius: 4
                        },
                        {
                            label: 'Realisasi (Rp)',
                            data: bReal,
                            backgroundColor: 'rgba(5, 150, 105, 0.85)',
                            borderColor: '#047857',
                            borderWidth: 1,
                            borderRadius: 4
                        }
                    ]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'top', labels: { boxWidth: 12, font: { size: 11 } } },
                        tooltip: {
                            callbacks: {
                                label: (ctx) => ctx.dataset.label + ': Rp ' + Math.round(ctx.parsed.x).toLocaleString('id-ID')
                            }
                        }
                    },
                    scales: {
                        x: {
                            beginAtZero: true,
                            ticks: {
                                callback: (v) => 'Rp ' + (v >= 1000000 ? (v/1000000).toFixed(0) + 'M' : (v/1000).toFixed(0) + 'K')
                            }
                        }
                    }
                }
            });
        }

        // 4. Chart Top Item Belanja GA Terbesar (Horizontal Bar)
        const topItems = stats.top_expense_items || [];
        const topLabels = topItems.map(t => t.item.length > 22 ? t.item.substring(0, 20) + '...' : t.item);
        const topAmounts = topItems.map(t => t.amount);

        const ctxTop = document.getElementById('chartGATopExp');
        if (ctxTop) {
            window.gaChartTopExp = new Chart(ctxTop, {
                type: 'bar',
                data: {
                    labels: topLabels,
                    datasets: [{
                        label: 'Nominal Belanja (Rp)',
                        data: topAmounts,
                        backgroundColor: 'rgba(245, 158, 11, 0.85)',
                        borderColor: '#D97706',
                        borderWidth: 1,
                        borderRadius: 4
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: (ctx) => 'Rp ' + Math.round(ctx.parsed.x).toLocaleString('id-ID')
                            }
                        }
                    },
                    scales: {
                        x: {
                            beginAtZero: true,
                            ticks: {
                                callback: (v) => 'Rp ' + (v >= 1000000 ? (v/1000000).toFixed(1) + 'M' : (v/1000).toFixed(0) + 'K')
                            }
                        }
                    }
                }
            });
        }
    }

    let G_GA_FILTERED_CACHE = [];
    let G_GA_PAGE = 1;
    let G_GA_PAGE_SIZE = 25;

    function onGATableFilterChange() {
        G_GA_PAGE = 1;
        filterGAData();
    }

    function onGAPageSizeChange() {
        const ps = document.getElementById('ga-table-pagesize') ? document.getElementById('ga-table-pagesize').value : '25';
        G_GA_PAGE_SIZE = ps === 'all' ? 999999 : parseInt(ps, 10);
        G_GA_PAGE = 1;
        filterGAData();
    }

    function resetGATableFilters() {
        if (document.getElementById('ga-table-quick-search')) document.getElementById('ga-table-quick-search').value = '';
        if (document.getElementById('ga-table-filter-unit')) document.getElementById('ga-table-filter-unit').value = '';
        if (document.getElementById('ga-table-filter-cat')) document.getElementById('ga-table-filter-cat').value = '';
        if (document.getElementById('ga-table-filter-nominal')) document.getElementById('ga-table-filter-nominal').value = '';
        if (document.getElementById('ga-table-filter-proof')) document.getElementById('ga-table-filter-proof').value = '';
        if (document.getElementById('ga-table-sort')) document.getElementById('ga-table-sort').value = 'date_desc';
        if (document.getElementById('ga-table-pagesize')) document.getElementById('ga-table-pagesize').value = '25';
        G_GA_PAGE = 1;
        G_GA_PAGE_SIZE = 25;
        filterGAData();
    }

    function gotoGAPage(pageNum) {
        G_GA_PAGE = pageNum;
        renderGAPaginatedTable();
    }

    function filterGAData() {
        const topCatFilter = document.getElementById('filter-ga-category') ? document.getElementById('filter-ga-category').value.trim() : '';
        const topSearch = document.getElementById('filter-ga-search') ? document.getElementById('filter-ga-search').value.toLowerCase().trim() : '';

        const tblSearch = document.getElementById('ga-table-quick-search') ? document.getElementById('ga-table-quick-search').value.toLowerCase().trim() : '';
        const tblUnit = document.getElementById('ga-table-filter-unit') ? document.getElementById('ga-table-filter-unit').value.trim() : '';
        const tblCat = document.getElementById('ga-table-filter-cat') ? document.getElementById('ga-table-filter-cat').value.trim() : '';
        const tblNominal = document.getElementById('ga-table-filter-nominal') ? document.getElementById('ga-table-filter-nominal').value.trim() : '';
        const tblProof = document.getElementById('ga-table-filter-proof') ? document.getElementById('ga-table-filter-proof').value.trim() : '';
        const sortMode = document.getElementById('ga-table-sort') ? document.getElementById('ga-table-sort').value : 'date_desc';

        const filtered = G_FINANCE_DATA.filter(item => {
            if (topCatFilter && item.main_category !== topCatFilter) return false;
            if (tblCat && !((item.main_category || '') + ' ' + (item.coa_name || '')).toUpperCase().includes(tblCat)) return false;

            if (tblUnit) {
                const u = (item.unit_target || '').toUpperCase();
                if (tblUnit === 'TK' && !u.includes('TK') && !u.includes('PGTK')) return false;
                else if (tblUnit !== 'TK' && !u.includes(tblUnit.toUpperCase())) return false;
            }

            const amt = item.amount || 0;
            if (tblNominal === 'gt_10m' && amt <= 10000000) return false;
            if (tblNominal === '1m_10m' && (amt < 1000000 || amt > 10000000)) return false;
            if (tblNominal === 'lt_1m' && amt >= 1000000) return false;

            if (tblProof === 'with_proof' && !item.drive_file_url) return false;
            if (tblProof === 'no_proof' && item.drive_file_url) return false;

            const combinedText = [
                item.description, item.vendor_name, item.coa_name,
                item.kb_code, item.reference_no, item.id, item.unit_target
            ].join(' ').toLowerCase();

            if (topSearch && !combinedText.includes(topSearch)) return false;
            if (tblSearch && !combinedText.includes(tblSearch)) return false;

            return true;
        });

        filtered.sort((a, b) => {
            if (sortMode === 'date_asc') return (a.transaction_date || '').localeCompare(b.transaction_date || '');
            if (sortMode === 'amount_desc') return (b.amount || 0) - (a.amount || 0);
            if (sortMode === 'amount_asc') return (a.amount || 0) - (b.amount || 0);
            return (b.transaction_date || '').localeCompare(a.transaction_date || '');
        });

        G_GA_FILTERED_CACHE = filtered;
        renderGAPaginatedTable();
    }

    function renderGAPaginatedTable() {
        const data = G_GA_FILTERED_CACHE;
        const tbody = document.getElementById('finance-table-tbody');
        const emptyState = document.getElementById('finance-empty-state');
        const countEl = document.getElementById('ga-table-count');
        const totalAmountEl = document.getElementById('ga-table-total-amount');
        const paginationInfo = document.getElementById('ga-pagination-info');
        const paginationBtns = document.getElementById('ga-pagination-buttons');

        if (!tbody) return;

        const totalFilteredAmount = data.reduce((acc, x) => acc + (x.amount || 0), 0);
        if (countEl) countEl.innerText = `${data.length}`;
        if (totalAmountEl) totalAmountEl.innerText = `Rp ${totalFilteredAmount.toLocaleString('id-ID')}`;

        if (data.length === 0) {
            tbody.innerHTML = '';
            if (emptyState) emptyState.classList.remove('hidden');
            if (paginationInfo) paginationInfo.innerText = 'Menampilkan 0 dari 0 transaksi';
            if (paginationBtns) paginationBtns.innerHTML = '';
            return;
        }

        if (emptyState) emptyState.classList.add('hidden');

        const totalRows = data.length;
        const pageSize = G_GA_PAGE_SIZE;
        const totalPages = Math.ceil(totalRows / pageSize) || 1;
        if (G_GA_PAGE > totalPages) G_GA_PAGE = totalPages;
        if (G_GA_PAGE < 1) G_GA_PAGE = 1;

        const startIndex = (G_GA_PAGE - 1) * pageSize;
        const endIndex = Math.min(startIndex + pageSize, totalRows);
        const pagedData = data.slice(startIndex, endIndex);

        if (paginationInfo) {
            paginationInfo.innerText = `Menampilkan ${startIndex + 1} - ${endIndex} dari ${totalRows} transaksi`;
        }

        if (paginationBtns) {
            let btnsHtml = '';
            if (G_GA_PAGE > 1) {
                btnsHtml += `<button type="button" onclick="gotoGAPage(${G_GA_PAGE - 1})" class="px-2.5 py-1 bg-white hover:bg-slate-100 border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 transition cursor-pointer flex items-center gap-1"><i class="fa-solid fa-chevron-left text-[10px]"></i> Sebelumnya</button>`;
            } else {
                btnsHtml += `<button type="button" disabled class="px-2.5 py-1 bg-slate-50 border border-slate-100 rounded-lg text-xs font-semibold text-slate-300 cursor-not-allowed">Sebelumnya</button>`;
            }

            btnsHtml += `<span class="px-3 py-1 font-bold text-xs text-slate-700 bg-white border border-slate-200 rounded-lg">${G_GA_PAGE} / ${totalPages}</span>`;

            if (G_GA_PAGE < totalPages) {
                btnsHtml += `<button type="button" onclick="gotoGAPage(${G_GA_PAGE + 1})" class="px-2.5 py-1 bg-white hover:bg-slate-100 border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 transition cursor-pointer flex items-center gap-1">Berikutnya <i class="fa-solid fa-chevron-right text-[10px]"></i></button>`;
            } else {
                btnsHtml += `<button type="button" disabled class="px-2.5 py-1 bg-slate-50 border border-slate-100 rounded-lg text-xs font-semibold text-slate-300 cursor-not-allowed">Berikutnya</button>`;
            }
            paginationBtns.innerHTML = btnsHtml;
        }

        let html = '';
        pagedData.forEach(item => {
            const nominal = item.amount || 0;
            const driveUrl = item.drive_file_url || '';
            const driveBtn = driveUrl ? `
                <a href="${driveUrl}" target="_blank" class="inline-flex items-center gap-1 px-2.5 py-1 bg-blue-50 text-blue-700 hover:bg-blue-100 rounded-lg text-[11px] font-semibold transition shadow-2xs" title="Buka Bukti di Google Drive">
                    <i class="fa-brands fa-google-drive text-amber-500"></i>
                    <span>Bukti</span>
                </a>
            ` : `<span class="text-slate-300 text-[11px]">-</span>`;

            html += `
            <tr class="hover:bg-slate-50/80 transition">
                <td class="py-3 px-4 font-mono">
                    <div class="font-bold text-slate-800">${item.transaction_date || '-'}</div>
                    <div class="text-[10px] text-slate-400 font-mono">${item.kb_code || item.id}</div>
                </td>
                <td class="py-3 px-4">
                    <div class="font-semibold text-slate-700 truncate max-w-[180px]" title="${item.coa_name || '-'}">${item.coa_name || '-'}</div>
                    <div class="text-[10px] text-emerald-600 font-mono">${item.coa_code || '-'}</div>
                </td>
                <td class="py-3 px-4">
                    <div class="font-semibold text-slate-800">${item.vendor_name || '-'}</div>
                    <div class="text-[10px] text-slate-400">${item.bank_info || item.reference_no || ''}</div>
                </td>
                <td class="py-3 px-4 max-w-xs">
                    <p class="text-slate-700 truncate font-medium" title="${item.description}">${item.description || '-'}</p>
                </td>
                <td class="py-3 px-4 text-right font-bold text-rose-700">
                    Rp ${nominal.toLocaleString('id-ID')}
                </td>
                <td class="py-3 px-4">
                    <span class="inline-block px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-700">${item.fund_source || '2. SPP'}</span>
                    <span class="inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-100 text-emerald-800 ml-1">${item.unit_target || 'Umum'}</span>
                </td>
                <td class="py-3 px-4">
                    <div class="font-medium text-slate-700">${item.reporter_name || 'Bu Rinni'}</div>
                    <div class="text-[10px] text-slate-400">${item.reporter_wa ? '+' + item.reporter_wa : ''}</div>
                </td>
                <td class="py-3 px-4 text-center">
                    ${driveBtn}
                </td>
                <td class="py-3 px-4 text-center">
                    <div class="inline-flex items-center gap-1">
                        <button type="button" onclick="openExpenseDetail('${item.id}')" class="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition cursor-pointer" title="Lihat Detail Transaksi">
                            <i class="fa-solid fa-eye text-xs"></i>
                        </button>
                        <button type="button" onclick="openEditExpenseModal('${item.id}')" class="p-1.5 text-amber-600 hover:text-amber-800 hover:bg-amber-50 rounded-lg transition cursor-pointer" title="Koreksi / Edit Transaksi">
                            <i class="fa-solid fa-pen-to-square text-xs"></i>
                        </button>
                    </div>
                </td>
            </tr>`;
        });

        tbody.innerHTML = html;
    }

    function exportGAExcel() {
        const startDate = document.getElementById('filter-ga-start-date') ? document.getElementById('filter-ga-start-date').value : '';
        const endDate = document.getElementById('filter-ga-end-date') ? document.getElementById('filter-ga-end-date').value : '';
        const cat = document.getElementById('filter-ga-category') ? document.getElementById('filter-ga-category').value : '';

        let url = '/api/ga/expenses/export?1=1';
        if (startDate) url += '&start_date=' + encodeURIComponent(startDate);
        if (endDate) url += '&end_date=' + encodeURIComponent(endDate);
        if (cat) url += '&category=' + encodeURIComponent(cat);

        window.open(url, '_blank');
    }

    function openExpenseDetail(expId) {
        const item = G_FINANCE_DATA.find(x => x.id === expId);
        if (!item) return;

        document.getElementById('detail-exp-title').innerText = item.id + ' — ' + (item.coa_name || 'Pengeluaran GA');

        let itemsHtml = '';
        if (item.items_json) {
            try {
                const parsed = JSON.parse(item.items_json);
                if (Array.isArray(parsed) && parsed.length > 0) {
                    itemsHtml += '<div class="mt-2 border-t border-slate-100 pt-2"><div class="font-bold text-slate-600 mb-1">Rincian Barang / Nota:</div><ul class="list-disc list-inside space-y-0.5 text-slate-700">';
                    parsed.forEach(p => {
                        const nama = p.nama_barang || p.nama || '-';
                        const qty = p.qty ? (p.qty + ' ' + (p.satuan || '')) : '';
                        itemsHtml += `<li>${nama} ${qty ? '(' + qty + ')' : ''}</li>`;
                    });
                    itemsHtml += '</ul></div>';
                }
            } catch (e) {}
        }

        const driveLinkHtml = item.drive_file_url ? `
            <div class="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-xl flex items-center justify-between">
                <div class="flex items-center gap-2">
                    <i class="fa-brands fa-google-drive text-amber-500 text-lg"></i>
                    <div>
                        <div class="font-bold text-blue-900">Arsip Bukti Transaksi</div>
                        <div class="text-[11px] text-blue-600">Tersimpan permanen di Google Drive</div>
                    </div>
                </div>
                <a href="${item.drive_file_url}" target="_blank" class="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold text-xs transition">
                    Lihat Berkas
                </a>
            </div>
        ` : '';

        const bodyHtml = `
            <div class="grid grid-cols-2 gap-2 p-3 bg-slate-50 rounded-xl">
                <div><span class="text-slate-400">Tanggal:</span> <strong class="text-slate-700">${item.transaction_date}</strong></div>
                <div><span class="text-slate-400">Nominal:</span> <strong class="text-rose-600 text-sm">Rp ${(item.amount || 0).toLocaleString('id-ID')}</strong></div>
                <div><span class="text-slate-400">Kode KB:</span> <code class="text-emerald-700 font-mono">${item.kb_code || '-'}</code></div>
                <div><span class="text-slate-400">Nomor Referensi:</span> <span class="text-slate-700 font-mono">${item.reference_no || '-'}</span></div>
                <div><span class="text-slate-400">Mata Anggaran:</span> <span class="text-slate-700">${item.coa_name} (${item.coa_code})</span></div>
                <div><span class="text-slate-400">Kategori Utama:</span> <span class="text-slate-700">${item.main_category}</span></div>
                <div><span class="text-slate-400">Sumber Dana:</span> <span class="text-slate-700">${item.fund_source || '2. SPP'}</span></div>
                <div><span class="text-slate-400">Unit Target:</span> <span class="text-slate-700">${item.unit_target || 'Umum'}</span></div>
                <div class="col-span-2"><span class="text-slate-400">Penerima / Toko:</span> <strong class="text-slate-800">${item.vendor_name || '-'}</strong> (${item.bank_info || '-'})</div>
            </div>

            <div class="p-3 bg-slate-50 rounded-xl">
                <span class="text-slate-400 block mb-1">Uraian / Keterangan:</span>
                <p class="text-slate-800 font-medium">${item.description || '-'}</p>
                ${itemsHtml}
            </div>

            ${driveLinkHtml}

            <div class="text-[11px] text-slate-400 pt-1 flex justify-between">
                <span>Pelapor: ${item.reporter_name || 'Bu Rinni'} (${item.reporter_wa || '-'})</span>
                <span>Sumber: ${item.source || 'WHATSAPP_BOT'}</span>
            </div>
        `;

        document.getElementById('detail-exp-body').innerHTML = bodyHtml;
        toggleModal('modal-finance-detail');
    }

    function openEditExpenseModal(expId) {
        const item = G_FINANCE_DATA.find(x => x.id === expId);
        if (!item) return;

        document.getElementById('edit-exp-id').value = item.id;
        document.getElementById('edit-exp-date').value = item.transaction_date || '';
        document.getElementById('edit-exp-amount').value = item.amount || 0;
        document.getElementById('edit-exp-vendor').value = item.vendor_name || '';
        document.getElementById('edit-exp-ref').value = item.reference_no || '';
        document.getElementById('edit-exp-desc').value = item.description || '';
        document.getElementById('edit-exp-coa').value = item.coa_code || '51412-006';
        document.getElementById('edit-exp-fund').value = item.fund_source || '2. SPP';
        document.getElementById('edit-exp-unit').value = item.unit_target || 'Umum';

        toggleModal('modal-finance-edit');
    }

    async function submitEditExpense(e) {
        e.preventDefault();
        const expId = document.getElementById('edit-exp-id').value;
        if (!expId) return;

        const btn = document.getElementById('btn-save-edit-expense');
        const origText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Menyimpan...';

        const payload = {
            transaction_date: document.getElementById('edit-exp-date').value,
            amount: parseInt(document.getElementById('edit-exp-amount').value) || 0,
            vendor_name: document.getElementById('edit-exp-vendor').value.trim(),
            reference_no: document.getElementById('edit-exp-ref').value.trim(),
            description: document.getElementById('edit-exp-desc').value.trim(),
            coa_code: document.getElementById('edit-exp-coa').value,
            fund_source: document.getElementById('edit-exp-fund').value,
            unit_target: document.getElementById('edit-exp-unit').value
        };

        try {
            const res = await fetch(`/api/ga/expenses/${expId}/update`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (data.success) {
                toggleModal('modal-finance-edit');
                loadKeuanganGA();
            } else {
                alert('Gagal menyimpan koreksi: ' + (data.error || 'Terjadi kesalahan'));
            }
        } catch (err) {
            alert('Kesalahan jaringan: ' + err.message);
        } finally {
            btn.disabled = false;
            btn.innerHTML = origText;
        }
    }

    async function deleteCurrentExpense() {
        const expId = document.getElementById('edit-exp-id').value;
        if (!expId) return;

        if (!confirm(`Yakin ingin menghapus transaksi ${expId}? Data pengeluaran ini akan dihapus permanen.`)) {
            return;
        }

        try {
            const res = await fetch(`/api/ga/expenses/${expId}/delete`, { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                toggleModal('modal-finance-edit');
                loadKeuanganGA();
            } else {
                alert('Gagal menghapus: ' + (data.error || 'Terjadi kesalahan'));
            }
        } catch (err) {
            alert('Kesalahan jaringan: ' + err.message);
        }
    }
</script>
"""
