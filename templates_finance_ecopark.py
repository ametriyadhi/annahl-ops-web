# -*- coding: utf-8 -*-
"""
templates_finance_ecopark.py - Komponen Tampilan HTML & JavaScript untuk Tab Keuangan Ciangsana Ecopark
An Nahl Islamic School - Dashboard Operasional note-umum
Mendukung Pencatatan Terpadu Kas Masuk (Omset) & Kas Keluar (Operasional FKP ECO 2026-2027),
Filter Dinamis di Atas Card, Kartu Metrik Adaptif, Dashboard Grafik Analitik Keuangan (Chart.js),
Diagnosa Analis Keuangan AI Eksekutif, Modal Input/Edit Koreksi, Modal Panduan Format WA, dan Ekspor Excel (.xlsx).
"""

TAB_KEUANGAN_ECOPARK_HTML = """
<!-- TAB KEUANGAN TERPADU CIANGSANA ECOPARK -->
<div id="tab-keuangan-ecopark" class="tab-content hidden space-y-6">

    <!-- 1. HEADER & ACTION BAR -->
    <div class="bg-white rounded-2xl shadow-xs border border-slate-200/80 p-4 sm:p-6">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
                <div class="flex items-center gap-2 flex-wrap">
                    <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 tracking-wider uppercase">Standar RKAS FKP ECO 2026–2027</span>
                    <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-indigo-100 text-indigo-700">Executive Financial Analytics</span>
                    <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-100 text-amber-800">Vision AI & GDrive Cloud</span>
                </div>
                <h2 class="text-base sm:text-2xl font-bold text-slate-800 flex items-center gap-2 mt-1.5">
                    <i class="fa-solid fa-tree text-emerald-600"></i>
                    Buku Kas & Analitik Keuangan Ciangsana Ecopark
                </h2>
                <p class="text-xs text-slate-500 mt-1">Laporan analitik komprehensif: Arus Kas Bulanan, Komposisi Omset, Evaluasi Serapan Belanja 6 Pos RKAS, dan Pemantauan Transaksi Real-Time.</p>
            </div>
            <div class="flex items-center gap-2 sm:gap-3 flex-wrap">
                <button type="button" onclick="loadKeuanganEcopark()" class="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl transition flex items-center gap-1.5 cursor-pointer">
                    <i class="fa-solid fa-arrows-rotate"></i>
                    <span>Refresh</span>
                </button>
                <a href="https://wa.me/6285139373029" target="_blank" class="inline-flex items-center gap-1.5 px-3 py-2 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-200 rounded-xl text-xs font-semibold transition cursor-pointer shadow-2xs" title="Buka Chat WhatsApp Bot An Nahl Ops">
                    <i class="fa-brands fa-whatsapp text-emerald-600 text-sm"></i>
                    <span>Japri Bot: 0851-3937-3029</span>
                </a>
                <button type="button" onclick="openCreateEcoModal('EXPENSE')" class="px-3.5 py-2 bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold rounded-xl shadow-xs transition flex items-center gap-1.5 cursor-pointer">
                    <i class="fa-solid fa-receipt"></i>
                    <span>+ Catat Belanja</span>
                </button>
                <button type="button" onclick="openCreateEcoModal('INCOME')" class="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-xl shadow-xs transition flex items-center gap-1.5 cursor-pointer">
                    <i class="fa-solid fa-hand-holding-dollar"></i>
                    <span>+ Catat Pemasukan</span>
                </button>
                <button type="button" onclick="toggleModal('modal-eco-format')" class="px-3 py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 text-xs font-semibold rounded-xl transition flex items-center gap-1.5 cursor-pointer">
                    <i class="fa-brands fa-whatsapp text-emerald-600"></i>
                    <span>Format WA</span>
                </button>
                <button type="button" onclick="exportEcoExcel()" class="px-3.5 py-2 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-200 text-xs font-semibold rounded-xl transition flex items-center gap-1.5 cursor-pointer shadow-2xs">
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
                    <div class="flex items-center gap-2">
                        <h3 class="text-xs font-bold text-slate-800 uppercase tracking-wider">Periode Analisis Finansial Ecopark</h3>
                        <span id="eco-stat-period-tag" class="text-[10px] px-2 py-0.5 rounded-full font-bold bg-emerald-100 text-emerald-800">Semua Periode Kumulatif</span>
                    </div>
                    <p class="text-[11px] text-slate-400 mt-0.5">Ubah rentang tanggal atau gunakan shortcut untuk menggerakkan kartu metrik dan grafik analitik.</p>
                </div>
            </div>

            <!-- Date Range Pickers & Shortcuts -->
            <div class="flex items-center gap-2 flex-wrap">
                <div class="flex items-center bg-slate-50 border border-slate-200 rounded-xl px-2.5 py-1.5 gap-2 shadow-2xs">
                    <div class="flex items-center gap-1 text-slate-500 text-xs font-medium">
                        <i class="fa-regular fa-calendar text-emerald-600 text-xs"></i>
                        <span>Dari:</span>
                    </div>
                    <input type="date" id="filter-eco-start-date" onchange="onEcoDateChange()" class="bg-transparent text-slate-700 text-xs font-semibold focus:outline-hidden cursor-pointer" title="Tanggal Mulai">
                    <span class="text-slate-300">|</span>
                    <div class="flex items-center gap-1 text-slate-500 text-xs font-medium">
                        <span>S/d:</span>
                    </div>
                    <input type="date" id="filter-eco-end-date" onchange="onEcoDateChange()" class="bg-transparent text-slate-700 text-xs font-semibold focus:outline-hidden cursor-pointer" title="Tanggal Selesai">
                    <button type="button" onclick="clearEcoDateFilter()" id="btn-eco-clear-date" class="text-slate-400 hover:text-rose-600 text-xs px-1 cursor-pointer transition" title="Reset Rentang Tanggal">
                        <i class="fa-solid fa-circle-xmark"></i>
                    </button>
                </div>

                <!-- Shortcut Presets -->
                <div class="inline-flex items-center bg-slate-100/80 p-0.5 rounded-xl text-[11px] font-semibold text-slate-600">
                    <button type="button" onclick="setEcoQuickDate('today')" class="px-2.5 py-1.5 rounded-lg hover:bg-white hover:text-slate-800 transition cursor-pointer">Hari Ini</button>
                    <button type="button" onclick="setEcoQuickDate('7days')" class="px-2.5 py-1.5 rounded-lg hover:bg-white hover:text-slate-800 transition cursor-pointer">7 Hari</button>
                    <button type="button" onclick="setEcoQuickDate('this_month')" class="px-2.5 py-1.5 rounded-lg hover:bg-white hover:text-slate-800 transition cursor-pointer">Bulan Ini</button>
                    <button type="button" onclick="setEcoQuickDate('all')" class="px-2.5 py-1.5 rounded-lg bg-white text-emerald-700 font-bold shadow-2xs transition cursor-pointer">Semua</button>
                </div>
            </div>
        </div>
    </div>

    <!-- 3. KARTU METRIK DINAMIS (RESPONSIF TERHADAP FILTER) -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <!-- 1. Total Pemasukan -->
        <div class="bg-emerald-50/50 border border-emerald-200/60 rounded-2xl p-4 shadow-2xs hover:shadow-xs transition">
            <div class="flex items-center justify-between text-emerald-700 text-xs font-semibold">
                <span>Kas Masuk (Omset)</span>
                <div class="w-7 h-7 rounded-lg bg-emerald-100 flex items-center justify-center text-emerald-600">
                    <i class="fa-solid fa-arrow-down-left text-xs"></i>
                </div>
            </div>
            <div id="eco-stat-income" class="text-xl sm:text-2xl font-bold text-emerald-800 mt-2">Rp 0</div>
            <div id="eco-stat-income-count" class="text-[11px] text-emerald-600 font-medium mt-1">0 Transaksi Penjualan / Sewa</div>
        </div>

        <!-- 2. Total Pengeluaran -->
        <div class="bg-rose-50/50 border border-rose-200/60 rounded-2xl p-4 shadow-2xs hover:shadow-xs transition">
            <div class="flex items-center justify-between text-rose-700 text-xs font-semibold">
                <span>Kas Keluar (Belanja)</span>
                <div class="w-7 h-7 rounded-lg bg-rose-100 flex items-center justify-center text-rose-600">
                    <i class="fa-solid fa-arrow-up-right text-xs"></i>
                </div>
            </div>
            <div id="eco-stat-expense" class="text-xl sm:text-2xl font-bold text-rose-800 mt-2">Rp 0</div>
            <div id="eco-stat-expense-count" class="text-[11px] text-rose-600 font-medium mt-1">0 Transaksi Operasional</div>
        </div>

        <!-- 3. Saldo Kas Bersih -->
        <div class="bg-indigo-50/50 border border-indigo-200/60 rounded-2xl p-4 shadow-2xs hover:shadow-xs transition">
            <div class="flex items-center justify-between text-indigo-700 text-xs font-semibold">
                <span>Saldo Kas Bersih</span>
                <div class="w-7 h-7 rounded-lg bg-indigo-100 flex items-center justify-center text-indigo-600">
                    <i class="fa-solid fa-wallet text-xs"></i>
                </div>
            </div>
            <div id="eco-stat-balance" class="text-xl sm:text-2xl font-bold text-indigo-800 mt-2">Rp 0</div>
            <div id="eco-stat-balance-desc" class="text-[11px] text-indigo-600 font-medium mt-1">Net Cashflow Juli 2026 s/d Kini</div>
        </div>

        <!-- 4. Kontrol Plafon RKAS -->
        <div class="bg-purple-50/50 border border-purple-200/60 rounded-2xl p-4 shadow-2xs hover:shadow-xs transition">
            <div class="flex items-center justify-between text-purple-700 text-xs font-semibold">
                <span>Plafon RKAS ECO</span>
                <div class="w-7 h-7 rounded-lg bg-purple-100 flex items-center justify-center text-purple-600">
                    <i class="fa-solid fa-chart-pie text-xs"></i>
                </div>
            </div>
            <div class="text-xl sm:text-2xl font-bold text-slate-800 mt-2">Rp 282.850.000</div>
            <div id="eco-stat-pct-serapan" class="text-[11px] text-purple-700 font-semibold mt-1">Serapan 0.0% dari Plafon</div>
        </div>
    </div>

    <!-- 4. CARD ANALIS KEUANGAN AIS (AI FINANCIAL ANALYST EXECUTIVE INSIGHTS) -->
    <div class="bg-white rounded-2xl shadow-xs border border-emerald-200/80 p-4 sm:p-5 space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3.5">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600 shadow-2xs shrink-0">
                    <i class="fa-solid fa-brain-circuit text-lg"></i>
                </div>
                <div>
                    <h3 class="text-sm sm:text-base font-bold text-slate-900 flex items-center gap-2">
                        Diagnosa & Analisis Keuangan Eksekutif (Ais Finance Intelligence)
                    </h3>
                    <p class="text-xs text-slate-500 font-medium mt-0.5">Penilaian otomatis kesehatan arus kas, struktur profitabilitas, dan pusat biaya Ecopark.</p>
                </div>
            </div>
            <div class="flex items-center gap-2 self-start sm:self-auto">
                <span class="text-xs font-semibold text-slate-500">Status Finansial:</span>
                <span id="ai-eco-status-badge" class="px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-1.5 shadow-2xs">
                    <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                    <span id="ai-eco-status-text">SURPLUS SEHAT</span>
                </span>
            </div>
        </div>

        <!-- 4 Mini Financial Ratios Cards -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div class="bg-emerald-50/60 rounded-xl p-3.5 border border-emerald-200/70">
                <div class="text-[11px] font-bold text-emerald-800 uppercase tracking-wider">Margin Surplus (Net)</div>
                <div id="ai-eco-margin" class="text-xl sm:text-2xl font-black text-emerald-900 mt-1">9.2%</div>
                <div class="text-[11px] text-emerald-700 font-medium mt-0.5">Persentase kas tersisa dari omset</div>
            </div>
            <div class="bg-amber-50/60 rounded-xl p-3.5 border border-amber-200/70">
                <div class="text-[11px] font-bold text-amber-800 uppercase tracking-wider">Operating Expense Ratio</div>
                <div id="ai-eco-oer" class="text-xl sm:text-2xl font-black text-amber-900 mt-1">90.8%</div>
                <div class="text-[11px] text-amber-700 font-medium mt-0.5">Proporsi belanja thd omset</div>
            </div>
            <div class="bg-blue-50/60 rounded-xl p-3.5 border border-blue-200/70">
                <div class="text-[11px] font-bold text-blue-800 uppercase tracking-wider">Kontributor Omset Utama</div>
                <div id="ai-eco-top-rev" class="text-xs sm:text-sm font-extrabold text-slate-900 truncate mt-1.5" title="Sewa Fasilitas (63.8%)">Sewa Fasilitas (63.8%)</div>
                <div class="text-[11px] text-blue-700 font-semibold mt-0.5 truncate">Kolam Aquatic & Futsal</div>
            </div>
            <div class="bg-rose-50/60 rounded-xl p-3.5 border border-rose-200/70">
                <div class="text-[11px] font-bold text-rose-800 uppercase tracking-wider">Pusat Beban Belanja</div>
                <div id="ai-eco-top-cost" class="text-xs sm:text-sm font-extrabold text-rose-900 truncate mt-1.5" title="PEMELIHARAAN (61.5%)">PEMELIHARAAN (61.5%)</div>
                <div class="text-[11px] text-rose-700 font-semibold mt-0.5 truncate">Fasilitas, Sarpras & BBM</div>
            </div>
        </div>

        <!-- Actionable Insights List -->
        <div class="bg-slate-50/90 rounded-xl p-4 border border-slate-200/80">
            <div class="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2.5 flex items-center gap-2">
                <i class="fa-solid fa-lightbulb text-amber-500"></i>
                <span>Catatan & Rekomendasi Analis Ais untuk Manajemen (Mr Slam & Tim):</span>
            </div>
            <ul id="ai-eco-insights-list" class="space-y-2 text-xs">
                <li class="flex items-start gap-2.5 text-slate-700 font-medium"><i class="fa-solid fa-circle-check text-emerald-600 mt-0.5 shrink-0 text-sm"></i><span>Memuat analisis eksekutif...</span></li>
            </ul>
        </div>
    </div>

    <!-- 5. DASHBOARD GRAFIK ANALITIK KEUANGAN (CHART.JS) -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-5">
        <!-- GRAFIK 1: Tren Arus Kas Bulanan (7 Cols) -->
        <div class="lg:col-span-7 bg-white rounded-2xl shadow-xs border border-slate-200/80 p-4 sm:p-5 flex flex-col justify-between">
            <div>
                <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                    <div>
                        <h3 class="text-sm font-bold text-slate-800 flex items-center gap-2">
                            <i class="fa-solid fa-chart-line text-emerald-600"></i>
                            Tren Arus Kas Bulanan (Omset vs Belanja vs Saldo)
                        </h3>
                        <p class="text-[11px] text-slate-400 mt-0.5">Komparasi pendapatan, pengeluaran, dan net cashflow per bulan TA 2026/2027.</p>
                    </div>
                    <span class="text-[10px] px-2 py-0.5 rounded-full font-semibold bg-slate-100 text-slate-600">Kumulatif</span>
                </div>
                <div class="relative h-64 sm:h-72 mt-3">
                    <canvas id="chart-eco-monthly-trend"></canvas>
                </div>
            </div>
            <div class="flex items-center justify-center gap-4 text-[11px] text-slate-500 pt-3 border-t border-slate-100 mt-2">
                <span class="flex items-center gap-1.5"><span class="w-3 h-3 rounded-sm bg-emerald-500 inline-block"></span> Kas Masuk (Omset)</span>
                <span class="flex items-center gap-1.5"><span class="w-3 h-3 rounded-sm bg-rose-500 inline-block"></span> Kas Keluar (Belanja)</span>
                <span class="flex items-center gap-1.5"><span class="w-3 h-0.5 bg-indigo-600 inline-block"></span> Saldo Kas Bersih</span>
            </div>
        </div>

        <!-- GRAFIK 2: Komposisi Sumber Pendapatan (5 Cols) -->
        <div class="lg:col-span-5 bg-white rounded-2xl shadow-xs border border-slate-200/80 p-4 sm:p-5 flex flex-col justify-between">
            <div>
                <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                    <div>
                        <h3 class="text-sm font-bold text-slate-800 flex items-center gap-2">
                            <i class="fa-solid fa-chart-pie text-emerald-600"></i>
                            Komposisi Sumber Pendapatan (Omset)
                        </h3>
                        <p class="text-[11px] text-slate-400 mt-0.5">Proporsi pemasukan per klaster produk & layanan Ecopark.</p>
                    </div>
                </div>
                <div class="relative h-64 sm:h-72 mt-3 flex items-center justify-center">
                    <canvas id="chart-eco-income-donut"></canvas>
                </div>
            </div>
            <div id="eco-donut-legend" class="grid grid-cols-2 gap-1 text-[11px] text-slate-600 pt-3 border-t border-slate-100 mt-2">
                <!-- Injected via JS -->
            </div>
        </div>

        <!-- GRAFIK 3: Evaluasi Realisasi vs Plafon 6 Pos RKAS (6 Cols) -->
        <div class="lg:col-span-6 bg-white rounded-2xl shadow-xs border border-slate-200/80 p-4 sm:p-5">
            <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                <div>
                    <h3 class="text-sm font-bold text-slate-800 flex items-center gap-2">
                        <i class="fa-solid fa-bars-progress text-purple-600"></i>
                        Evaluasi Realisasi vs Plafon 6 Pos FKP ECO 2026–2027
                    </h3>
                    <p class="text-[11px] text-slate-400 mt-0.5">Monitoring batas plafon anggaran tahunan Rp 282.85M.</p>
                </div>
            </div>
            <div class="relative h-64 sm:h-72 mt-3">
                <canvas id="chart-eco-budget-bars"></canvas>
            </div>
        </div>

        <!-- GRAFIK 4: Top 8 Beban Pengeluaran Operasional Terbesar (6 Cols) -->
        <div class="lg:col-span-6 bg-white rounded-2xl shadow-xs border border-slate-200/80 p-4 sm:p-5">
            <div class="flex items-center justify-between border-b border-slate-100 pb-3">
                <div>
                    <h3 class="text-sm font-bold text-slate-800 flex items-center gap-2">
                        <i class="fa-solid fa-cart-shopping text-rose-600"></i>
                        Top 8 Item Beban Pengeluaran Operasional Terbesar
                    </h3>
                    <p class="text-[11px] text-slate-400 mt-0.5">Rincian item belanja yang paling banyak menyerap anggaran operasional.</p>
                </div>
            </div>
            <div class="relative h-64 sm:h-72 mt-3">
                <canvas id="chart-eco-top-expense"></canvas>
            </div>
        </div>
    </div>

    <!-- 6. KONTROL 6 POS MATA ANGGARAN UTAMA (MINI CONTROL BARS) -->
    <div class="bg-white rounded-2xl shadow-xs border border-slate-200/80 p-4 sm:p-5 space-y-3.5">
        <div class="flex items-center justify-between">
            <h3 class="text-xs font-bold text-slate-600 uppercase tracking-wider flex items-center gap-2">
                <i class="fa-solid fa-layer-group text-slate-400"></i>
                Detail Alokasi & Sisa Saldo 6 Pos Anggaran FKP ECO
            </h3>
            <span class="text-[11px] text-slate-400">Plafon Tahunan: Rp 282.850.000</span>
        </div>
        <div id="eco-categories-container" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3">
            <div class="text-center py-4 text-xs text-slate-400 col-span-full">Memuat alokasi anggaran RKAS Ecopark...</div>
        </div>
    </div>

    <!-- 7. TABEL DATA TRANSAKSI LENGKAP -->
    <div class="bg-white rounded-2xl shadow-xs border border-slate-200/80 overflow-hidden">
        <!-- Sub-Header Title & Live Stats -->
        <div class="p-4 sm:p-5 border-b border-slate-100 flex flex-col md:flex-row md:items-center justify-between gap-3">
            <div>
                <h3 class="text-sm font-bold text-slate-800 flex items-center gap-2">
                    <i class="fa-solid fa-list-check text-emerald-600"></i>
                    <span>Buku Jurnal Transaksi Keuangan Ecopark</span>
                </h3>
                <p class="text-xs text-slate-500 mt-0.5">
                    Menampilkan <span id="lbl-table-count" class="font-bold text-emerald-700">0</span> transaksi | Total Nilai: <span id="lbl-table-total" class="font-bold text-slate-800">Rp 0</span>
                </p>
            </div>
            <!-- Quick Table Search & Reset -->
            <div class="flex items-center gap-2 flex-wrap">
                <div class="relative w-full sm:w-64">
                    <input type="text" id="eco-table-quick-search" oninput="onEcoTableFilterChange()" placeholder="Cari uraian, toko/pembeli, ID..." class="w-full pl-9 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-700 focus:ring-2 focus:ring-emerald-500 focus:outline-hidden">
                    <i class="fa-solid fa-magnifying-glass absolute left-3 top-2.5 text-slate-400 text-xs"></i>
                </div>
                <button type="button" onclick="resetEcoTableFilters()" class="px-2.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-xl text-xs font-semibold transition cursor-pointer flex items-center gap-1" title="Reset Filter Tabel">
                    <i class="fa-solid fa-rotate-left"></i>
                    <span>Reset</span>
                </button>
            </div>
        </div>

        <!-- In-Table Multi-Filter Bar -->
        <div class="bg-slate-50/70 p-3 sm:px-5 border-b border-slate-200/70 flex flex-wrap items-center justify-between gap-2.5 text-xs">
            <div class="flex flex-wrap items-center gap-2">
                <!-- Filter Tipe Transaksi (Semua / Masuk / Keluar) -->
                <div class="flex items-center gap-1">
                    <span class="text-[11px] font-semibold text-slate-500">Tipe:</span>
                    <select id="eco-table-filter-type" onchange="onEcoTableFilterChange()" class="px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-medium text-slate-700 focus:outline-hidden">
                        <option value="">Semua Tipe</option>
                        <option value="INCOME">🟢 Kas Masuk (Omset)</option>
                        <option value="EXPENSE">🔴 Kas Keluar (Belanja)</option>
                    </select>
                </div>

                <!-- Filter Kategori / Klaster -->
                <div class="flex items-center gap-1">
                    <span class="text-[11px] font-semibold text-slate-500">Klaster / Pos:</span>
                    <select id="eco-table-filter-cat" onchange="onEcoTableFilterChange()" class="px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-medium text-slate-700 focus:outline-hidden">
                        <option value="">Semua Klaster & Pos</option>
                        <option value="Sewa Fasilitas">🏊‍♂️ Sewa Fasilitas (Kolam & Futsal)</option>
                        <option value="Edukasi">🎓 Edukasi & Event</option>
                        <option value="Panen Buah">🥭 Panen Buah</option>
                        <option value="Panen Sayur">🥬 Panen Sayur</option>
                        <option value="Ternak">🥚 Ternak & Telur</option>
                        <option value="52111">52111 Budidaya</option>
                        <option value="52121">52121 Peternakan</option>
                        <option value="52131">52131 Pemeliharaan</option>
                        <option value="52132">52132 Kunjungan</option>
                        <option value="52133">52133 Marketing</option>
                        <option value="52134">52134 Investasi</option>
                    </select>
                </div>

                <!-- Filter Bukti Nota -->
                <div class="flex items-center gap-1">
                    <span class="text-[11px] font-semibold text-slate-500">Bukti:</span>
                    <select id="eco-table-filter-proof" onchange="onEcoTableFilterChange()" class="px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-medium text-slate-700 focus:outline-hidden">
                        <option value="">Semua</option>
                        <option value="with_proof">📸 Ada Bukti Drive</option>
                        <option value="no_proof">Tanpa Bukti</option>
                    </select>
                </div>

                <!-- Filter Nominal -->
                <div class="flex items-center gap-1">
                    <span class="text-[11px] font-semibold text-slate-500">Nominal:</span>
                    <select id="eco-table-filter-nominal" onchange="onEcoTableFilterChange()" class="px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-medium text-slate-700 focus:outline-hidden">
                        <option value="">Semua Nominal</option>
                        <option value="gt_1m">> Rp 1 Juta</option>
                        <option value="100k_1m">Rp 100 Ribu s/d 1 Juta</option>
                        <option value="lt_100k">< Rp 100 Ribu</option>
                    </select>
                </div>
            </div>

            <!-- Sorting & Rows Per Page -->
            <div class="flex items-center gap-2">
                <div class="flex items-center gap-1">
                    <span class="text-[11px] font-semibold text-slate-500">Urutkan:</span>
                    <select id="eco-table-sort" onchange="onEcoTableFilterChange()" class="px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-medium text-slate-700 focus:outline-hidden">
                        <option value="date_desc">Tanggal Terbaru</option>
                        <option value="date_asc">Tanggal Terlama</option>
                        <option value="amount_desc">Nominal Terbesar</option>
                        <option value="amount_asc">Nominal Terkecil</option>
                    </select>
                </div>

                <div class="flex items-center gap-1">
                    <span class="text-[11px] font-semibold text-slate-500">Baris:</span>
                    <select id="eco-table-pagesize" onchange="onEcoPageSizeChange()" class="px-2 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-medium text-slate-700 focus:outline-hidden">
                        <option value="25">25</option>
                        <option value="50">50</option>
                        <option value="100">100</option>
                        <option value="all">Semua</option>
                    </select>
                </div>
            </div>
        </div>

        <div class="overflow-x-auto">
            <table class="w-full text-left border-collapse min-w-[900px]">
                <thead>
                    <tr class="bg-slate-50/75 border-b border-slate-200/80 text-[11px] font-bold text-slate-600 uppercase tracking-wider">
                        <th class="py-3 px-4">Tgl & ID</th>
                        <th class="py-3 px-3">Tipe & Kategori</th>
                        <th class="py-3 px-4">Uraian Transaksi</th>
                        <th class="py-3 px-3">Toko / Pembeli</th>
                        <th class="py-3 px-3 text-right">Nominal (Rp)</th>
                        <th class="py-3 px-3 text-center">Metode</th>
                        <th class="py-3 px-3 text-center">Bukti Nota</th>
                        <th class="py-3 px-3 text-center">Aksi</th>
                    </tr>
                </thead>
                <tbody id="eco-table-body" class="divide-y divide-slate-100 text-xs">
                    <tr>
                        <td colspan="8" class="text-center py-8 text-slate-400">
                            <i class="fa-solid fa-spinner fa-spin text-xl text-emerald-600 mb-2"></i>
                            <div>Memuat data transaksi Ecopark...</div>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Table Pagination Footer -->
        <div id="eco-table-pagination" class="p-3.5 border-t border-slate-100 bg-slate-50/50 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-500">
            <div id="eco-pagination-info">Menampilkan 0 - 0 dari 0 transaksi</div>
            <div class="flex items-center gap-1" id="eco-pagination-buttons">
                <!-- Injected via JS -->
            </div>
        </div>
    </div>

</div>

<!-- MODAL INPUT TRANSAKSI BARU -->
<div id="modal-eco-create" class="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 hidden">
    <div class="bg-white rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden border border-slate-100 animate-in fade-in zoom-in-95 duration-150 max-h-[90vh] flex flex-col">
        <div class="p-4 sm:p-5 bg-gradient-to-r from-emerald-700 to-teal-800 text-white flex items-center justify-between">
            <div class="flex items-center gap-2.5">
                <div class="w-8 h-8 rounded-lg bg-white/20 flex items-center justify-center text-white">
                    <i id="create-eco-modal-icon" class="fa-solid fa-receipt"></i>
                </div>
                <div>
                    <h3 id="create-eco-modal-title" class="font-bold text-sm sm:text-base">Catat Transaksi Ecopark</h3>
                    <p class="text-[11px] text-emerald-100">Pencatatan kas masuk & kas keluar standar RKAS FKP ECO</p>
                </div>
            </div>
            <button type="button" onclick="toggleModal('modal-eco-create')" class="text-white/80 hover:text-white cursor-pointer text-lg">
                <i class="fa-solid fa-xmark"></i>
            </button>
        </div>

        <form id="form-create-eco" onsubmit="submitCreateEco(event)" class="p-4 sm:p-5 space-y-3.5 overflow-y-auto flex-1">
            <input type="hidden" id="create-eco-type" value="EXPENSE">

            <!-- Toggle Pilihan Tipe Transaksi -->
            <div>
                <label class="block text-xs font-semibold text-slate-700 mb-1">Tipe Transaksi</label>
                <div class="grid grid-cols-2 gap-2">
                    <button type="button" onclick="toggleCreateType('EXPENSE')" id="btn-create-type-expense" class="py-2 px-3 rounded-xl border text-xs font-bold transition flex items-center justify-center gap-1.5 border-rose-500 bg-rose-50 text-rose-800">
                        <i class="fa-solid fa-arrow-up-right"></i>
                        <span>Kas Keluar (Belanja)</span>
                    </button>
                    <button type="button" onclick="toggleCreateType('INCOME')" id="btn-create-type-income" class="py-2 px-3 rounded-xl border text-xs font-bold transition flex items-center justify-center gap-1.5 border-slate-200 bg-white text-slate-600 hover:bg-slate-50">
                        <i class="fa-solid fa-arrow-down-left"></i>
                        <span>Kas Masuk (Omset)</span>
                    </button>
                </div>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                    <label class="block text-xs font-semibold text-slate-700 mb-1">Tanggal Transaksi</label>
                    <input type="date" id="create-eco-date" required class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-700 focus:ring-2 focus:ring-emerald-500 focus:outline-hidden">
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-700 mb-1">Nominal (Rp)</label>
                    <input type="number" id="create-eco-amount" min="1" step="1" required placeholder="Contoh: 350000" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-700 focus:ring-2 focus:ring-emerald-500 focus:outline-hidden font-semibold">
                </div>
            </div>

            <!-- Pos Anggaran FKP ECO (Hanya untuk Expense) -->
            <div id="wrap-create-coa">
                <label class="block text-xs font-semibold text-slate-700 mb-1">Pos Mata Anggaran FKP ECO</label>
                <select id="create-eco-coa" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-700 focus:ring-2 focus:ring-emerald-500 focus:outline-hidden">
                    <option value="">-- Pilih Pos Anggaran FKP ECO --</option>
                </select>
            </div>

            <!-- Kategori Omset (Hanya untuk Income) -->
            <div id="wrap-create-income-cat" class="hidden">
                <label class="block text-xs font-semibold text-slate-700 mb-1">Kategori Pendapatan (Omset)</label>
                <select id="create-eco-income-cat" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-700 focus:ring-2 focus:ring-emerald-500 focus:outline-hidden">
                    <option value="Sewa Fasilitas">Sewa Fasilitas (Kolam Aquatic / Lapangan / ISBI)</option>
                    <option value="Sayuran">Hasil Panen Sayuran</option>
                    <option value="Telur">Hasil Telur Ternak</option>
                    <option value="Buah">Hasil Buah Sunnah & Lokal</option>
                    <option value="Ternak">Hasil Daging Ternak</option>
                    <option value="Kunjungan Edukasi">Kunjungan Edukasi & Outbound</option>
                    <option value="Kelas Edukasi">Kelas Edukasi / Workshop</option>
                    <option value="Lain-lain">Lain-lain</option>
                </select>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                    <label id="lbl-create-pihak" class="block text-xs font-semibold text-slate-700 mb-1">Nama Toko / Penjual</label>
                    <input type="text" id="create-eco-pihak" placeholder="Contoh: Toko Pakan Berkah" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-700 focus:ring-2 focus:ring-emerald-500 focus:outline-hidden">
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-700 mb-1">Metode Pembayaran</label>
                    <select id="create-eco-method" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-700 focus:ring-2 focus:ring-emerald-500 focus:outline-hidden">
                        <option value="Cash">Cash (Tunai)</option>
                        <option value="Transfer">Transfer Bank / QRIS</option>
                    </select>
                </div>
            </div>

            <div>
                <label class="block text-xs font-semibold text-slate-700 mb-1">Uraian / Deskripsi Rincian</label>
                <textarea id="create-eco-desc" rows="2" required placeholder="Contoh: Pembelian Pur GT 1 karung & dedak untuk bebek petelur" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-700 focus:ring-2 focus:ring-emerald-500 focus:outline-hidden"></textarea>
            </div>

            <div class="pt-2 flex items-center justify-end gap-2 border-t border-slate-100">
                <button type="button" onclick="toggleModal('modal-eco-create')" class="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl transition cursor-pointer">Batal</button>
                <button type="submit" id="btn-save-create-eco" class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-xl shadow-xs transition flex items-center gap-1.5 cursor-pointer">
                    <i class="fa-solid fa-check"></i>
                    <span>Simpan Transaksi</span>
                </button>
            </div>
        </form>
    </div>
</div>

<!-- MODAL EDIT KOREKSI TRANSAKSI -->
<div id="modal-eco-edit" class="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 hidden">
    <div class="bg-white rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden border border-slate-100 animate-in fade-in zoom-in-95 duration-150 max-h-[90vh] flex flex-col">
        <div class="p-4 sm:p-5 bg-slate-900 text-white flex items-center justify-between">
            <div class="flex items-center gap-2.5">
                <div class="w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
                    <i class="fa-solid fa-pen-to-square"></i>
                </div>
                <div>
                    <h3 class="font-bold text-sm sm:text-base">Koreksi Transaksi Ecopark</h3>
                    <p id="edit-eco-id-display" class="text-[11px] text-slate-400">ID: ECO-TRX-...</p>
                </div>
            </div>
            <button type="button" onclick="toggleModal('modal-eco-edit')" class="text-white/80 hover:text-white cursor-pointer text-lg">
                <i class="fa-solid fa-xmark"></i>
            </button>
        </div>

        <form id="form-edit-eco" onsubmit="submitEditEco(event)" class="p-4 sm:p-5 space-y-3.5 overflow-y-auto flex-1">
            <input type="hidden" id="edit-eco-id">
            <input type="hidden" id="edit-eco-type">

            <div class="flex items-center justify-between bg-slate-50 p-2.5 rounded-xl border border-slate-200">
                <span class="text-xs text-slate-500 font-semibold">Tipe Transaksi:</span>
                <span id="edit-eco-type-badge"></span>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                    <label class="block text-xs font-semibold text-slate-700 mb-1">Tanggal Transaksi</label>
                    <input type="date" id="edit-eco-date" required class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-700 focus:ring-2 focus:ring-emerald-500 focus:outline-hidden">
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-700 mb-1">Nominal (Rp)</label>
                    <input type="number" id="edit-eco-amount" min="1" step="1" required class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-700 focus:ring-2 focus:ring-emerald-500 focus:outline-hidden font-semibold">
                </div>
            </div>

            <div id="wrap-edit-coa">
                <label class="block text-xs font-semibold text-slate-700 mb-1">Pos Mata Anggaran FKP ECO</label>
                <select id="edit-eco-coa" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-700 focus:ring-2 focus:ring-emerald-500 focus:outline-hidden">
                    <option value="">-- Pilih Pos Anggaran FKP ECO --</option>
                </select>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                    <label id="lbl-edit-pihak" class="block text-xs font-semibold text-slate-700 mb-1">Toko / Pembeli</label>
                    <input type="text" id="edit-eco-pihak" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-700 focus:ring-2 focus:ring-emerald-500 focus:outline-hidden">
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-700 mb-1">Metode Pembayaran</label>
                    <select id="edit-eco-method" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-700 focus:ring-2 focus:ring-emerald-500 focus:outline-hidden">
                        <option value="Cash">Cash (Tunai)</option>
                        <option value="Transfer">Transfer Bank / QRIS</option>
                    </select>
                </div>
            </div>

            <div>
                <label class="block text-xs font-semibold text-slate-700 mb-1">Uraian / Deskripsi Rincian</label>
                <textarea id="edit-eco-desc" rows="2" required class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-700 focus:ring-2 focus:ring-emerald-500 focus:outline-hidden"></textarea>
            </div>

            <div class="pt-2 flex items-center justify-between border-t border-slate-100">
                <button type="button" onclick="deleteEcoTransactionCurrent()" class="px-3 py-2 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 text-xs font-semibold rounded-xl transition flex items-center gap-1 cursor-pointer">
                    <i class="fa-solid fa-trash"></i>
                    <span>Hapus</span>
                </button>
                <div class="flex items-center gap-2">
                    <button type="button" onclick="toggleModal('modal-eco-edit')" class="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl transition cursor-pointer">Batal</button>
                    <button type="submit" id="btn-save-edit-eco" class="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-xl shadow-xs transition flex items-center gap-1.5 cursor-pointer">
                        <i class="fa-solid fa-check"></i>
                        <span>Simpan Perubahan</span>
                    </button>
                </div>
            </div>
        </form>
    </div>
</div>

<!-- MODAL PREVIEW BUKTI GAMBAR -->
<div id="modal-eco-image" class="fixed inset-0 z-50 bg-slate-900/80 backdrop-blur-xs flex items-center justify-center p-4 hidden">
    <div class="bg-white rounded-2xl shadow-2xl max-w-xl w-full overflow-hidden border border-slate-100 animate-in fade-in zoom-in-95 duration-150 flex flex-col max-h-[90vh]">
        <div class="p-3.5 bg-slate-900 text-white flex items-center justify-between">
            <h3 id="eco-image-title" class="font-bold text-xs truncate max-w-md">Bukti Struk Transaksi Ecopark</h3>
            <button type="button" onclick="toggleModal('modal-eco-image')" class="text-white/80 hover:text-white cursor-pointer text-lg">
                <i class="fa-solid fa-xmark"></i>
            </button>
        </div>
        <div class="p-4 overflow-auto flex-1 flex items-center justify-center bg-slate-950">
            <img id="eco-image-src" src="" alt="Bukti Transaksi" class="max-h-[70vh] max-w-full rounded-lg object-contain shadow-lg">
        </div>
        <div class="p-3 bg-slate-100 border-t border-slate-200 flex items-center justify-between text-xs text-slate-600">
            <span>Tersimpan aman di Google Drive Cloud</span>
            <a id="eco-image-drive-link" href="#" target="_blank" class="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-lg transition flex items-center gap-1">
                <i class="fa-solid fa-arrow-up-right-from-square"></i>
                <span>Buka di Google Drive</span>
            </a>
        </div>
    </div>
</div>

<!-- MODAL PANDUAN FORMAT LAPORAN WA -->
<div id="modal-eco-format" class="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 hidden">
    <div class="bg-white rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden border border-slate-100 animate-in fade-in zoom-in-95 duration-150 max-h-[90vh] flex flex-col">
        <div class="p-4 sm:p-5 bg-gradient-to-r from-emerald-800 to-teal-900 text-white flex items-center justify-between">
            <div class="flex items-center gap-2.5">
                <div class="w-8 h-8 rounded-lg bg-white/20 flex items-center justify-center text-white">
                    <i class="fa-brands fa-whatsapp text-lg"></i>
                </div>
                <div>
                    <h3 class="font-bold text-sm sm:text-base">Panduan Format WhatsApp Tim Ecopark</h3>
                    <p class="text-[11px] text-emerald-100">Kirim format ini ke bot WA An Nahl Ops (0851-3937-3029)</p>
                </div>
            </div>
            <button type="button" onclick="toggleModal('modal-eco-format')" class="text-white/80 hover:text-white cursor-pointer text-lg">
                <i class="fa-solid fa-xmark"></i>
            </button>
        </div>

        <div class="p-4 sm:p-5 space-y-4 overflow-y-auto flex-1 text-xs">
            <div class="p-3 bg-emerald-50 rounded-xl border border-emerald-200/80">
                <div class="font-bold text-emerald-800 flex items-center gap-1.5 mb-1">
                    <i class="fa-solid fa-bolt text-emerald-600"></i>
                    <span>Praktis dengan Foto Struk / Screenshot Transfer:</span>
                </div>
                <p class="text-slate-600 text-[11px]">Cukup jepret foto struk belanja / bukti transfer m-banking, lalu kirim ke nomor bot WhatsApp (<b>0851-3937-3029</b>) dengan caption <b>#belanja_ecopark</b> atau <b>#pemasukan_ecopark</b>. Vision AI akan otomatis mengurai detailnya!</p>
            </div>

            <div class="space-y-1.5">
                <div class="flex items-center justify-between font-bold text-slate-700">
                    <span class="flex items-center gap-1.5 text-rose-700">
                        <i class="fa-solid fa-arrow-up-right"></i>
                        Format Kas Keluar (Belanja / Operasional)
                    </span>
                    <button type="button" onclick="copyFormatText('fmt-belanja')" class="text-[11px] text-indigo-600 hover:text-indigo-800 font-semibold cursor-pointer">Salin</button>
                </div>
                <pre id="fmt-belanja" class="p-3 bg-slate-900 text-emerald-400 rounded-xl font-mono text-[11px] whitespace-pre-wrap select-all cursor-pointer">#belanja_ecopark
Tanggal: Hari ini
Pos: Peternakan
Barang: Pur GT 1 Karung & Dedak
Nominal: 395000
Toko: Toko Pakan Berkah
Metode: Cash
Keterangan: Pakan ayam & bebek petelur</pre>
            </div>

            <div class="space-y-1.5">
                <div class="flex items-center justify-between font-bold text-slate-700">
                    <span class="flex items-center gap-1.5 text-emerald-700">
                        <i class="fa-solid fa-arrow-down-left"></i>
                        Format Kas Masuk (Omset / Sewa / Panen)
                    </span>
                    <button type="button" onclick="copyFormatText('fmt-pemasukan')" class="text-[11px] text-indigo-600 hover:text-indigo-800 font-semibold cursor-pointer">Salin</button>
                </div>
                <pre id="fmt-pemasukan" class="p-3 bg-slate-900 text-teal-400 rounded-xl font-mono text-[11px] whitespace-pre-wrap select-all cursor-pointer">#pemasukan_ecopark
Tanggal: Hari ini
Kategori: Sewa Fasilitas
Uraian: Sewa Kolam Renang (Fee Aquatic Therapy)
Pembeli: Siti Tri Hutami
Nominal: 500000
Metode: Transfer
Keterangan: Sesi terapi renang pekan ke-2</pre>
            </div>
        </div>

        <div class="p-3 bg-slate-50 border-t border-slate-100 flex justify-end">
            <button type="button" onclick="toggleModal('modal-eco-format')" class="px-4 py-2 bg-slate-800 hover:bg-slate-900 text-white text-xs font-semibold rounded-xl transition cursor-pointer">Tutup</button>
        </div>
    </div>
</div>
"""

JS_KEUANGAN_ECOPARK_SCRIPTS = """
<script>
    let G_ECO_DATA = [];
    let G_ECO_COA = [];
    let G_ECO_TYPE_FILTER = '';
    let G_ECO_SEARCH_TIMER = null;

    // Chart.js global instances
    window.ecoChartTrend = null;
    window.ecoChartIncome = null;
    window.ecoChartBudget = null;
    window.ecoChartTopExp = null;

    function onEcoDateChange() {
        loadKeuanganEcopark();
    }

    function clearEcoDateFilter() {
        const sEl = document.getElementById('filter-eco-start-date');
        const eEl = document.getElementById('filter-eco-end-date');
        if (sEl) sEl.value = '';
        if (eEl) eEl.value = '';
        loadKeuanganEcopark();
    }

    function setEcoQuickDate(preset) {
        const sEl = document.getElementById('filter-eco-start-date');
        const eEl = document.getElementById('filter-eco-end-date');
        if (!sEl || !eEl) return;

        const now = new Date();
        const formatDate = (d) => {
            const yr = d.getFullYear();
            const mo = String(d.getMonth() + 1).padStart(2, '0');
            const da = String(d.getDate()).padStart(2, '0');
            return `${yr}-${mo}-${da}`;
        };

        if (preset === 'today') {
            const todayStr = formatDate(now);
            sEl.value = todayStr;
            eEl.value = todayStr;
        } else if (preset === '7days') {
            const past = new Date();
            past.setDate(past.getDate() - 7);
            sEl.value = formatDate(past);
            eEl.value = formatDate(now);
        } else if (preset === 'this_month') {
            const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
            sEl.value = formatDate(firstDay);
            eEl.value = formatDate(now);
        } else if (preset === 'all') {
            sEl.value = '';
            eEl.value = '';
        }
        loadKeuanganEcopark();
    }

    async function loadKeuanganEcopark() {
        try {
            // 1. Fetch COA Master jika belum ada
            if (G_ECO_COA.length === 0) {
                const resCoa = await fetch('/api/eco/coa');
                if (resCoa.ok) {
                    const cData = await resCoa.json();
                    if (cData.success) {
                        G_ECO_COA = cData.data || [];
                        populateEcoCoaDropdowns();
                    }
                }
            }

            // 2. Build Query Params berdasarkan Filter Tanggal
            const startDate = document.getElementById('filter-eco-start-date') ? document.getElementById('filter-eco-start-date').value : '';
            const endDate = document.getElementById('filter-eco-end-date') ? document.getElementById('filter-eco-end-date').value : '';

            let queryParams = [];
            if (startDate) queryParams.push('start_date=' + encodeURIComponent(startDate));
            if (endDate) queryParams.push('end_date=' + encodeURIComponent(endDate));
            const qStr = queryParams.length ? '?' + queryParams.join('&') : '';

            // 3. Fetch Stats & Analytics
            const resStats = await fetch('/api/eco/stats' + qStr);
            if (resStats.ok) {
                const sData = await resStats.json();
                if (sData.success) {
                    renderEcoStats(sData);
                    renderEcoCharts(sData);
                }
            }

            // 4. Fetch Transactions
            let url = '/api/eco/transactions?limit=1000' + (qStr ? '&' + queryParams.join('&') : '');
            const resTrx = await fetch(url);
            if (resTrx.ok) {
                const tData = await resTrx.json();
                if (tData.success) {
                    G_ECO_DATA = tData.data || [];
                    filterEcoData();
                }
            }
        } catch (err) {
            console.error('Error loadKeuanganEcopark:', err);
        }
    }

    function populateEcoCoaDropdowns() {
        const createSel = document.getElementById('create-eco-coa');
        const editSel = document.getElementById('edit-eco-coa');
        if (!createSel || !editSel) return;

        let html = '<option value="">-- Pilih Pos Anggaran FKP ECO --</option>';
        let curParent = '';

        G_ECO_COA.forEach(c => {
            if (c.is_parent) {
                if (curParent) html += '</optgroup>';
                curParent = c.coa_name;
                html += `<optgroup label="${c.coa_code} ${c.coa_name} (Plafon Rp ${(c.budget_annual/1000000).toFixed(1)}M)">`;
            } else {
                html += `<option value="${c.coa_code}">${c.coa_code} - ${c.coa_name}</option>`;
            }
        });
        if (curParent) html += '</optgroup>';

        createSel.innerHTML = html;
        editSel.innerHTML = html;
    }

    function renderEcoStats(stats) {
        const sum = stats.summary || {};
        const inc = sum.total_income || 0;
        const exp = sum.total_expense || 0;
        const bal = sum.saldo_kas || 0;
        const pct = sum.overall_pct || 0;
        const ai = stats.ai_analysis || {};

        const startDate = document.getElementById('filter-eco-start-date') ? document.getElementById('filter-eco-start-date').value : '';
        const endDate = document.getElementById('filter-eco-end-date') ? document.getElementById('filter-eco-end-date').value : '';
        const tagEl = document.getElementById('eco-stat-period-tag');
        const balDescEl = document.getElementById('eco-stat-balance-desc');

        let periodLabel = 'Semua Periode (Juli 2026 s/d Kini)';
        let isFiltered = false;

        if (startDate && endDate) {
            if (startDate === endDate) {
                periodLabel = `Tanggal: ${startDate}`;
            } else {
                periodLabel = `${startDate} s/d ${endDate}`;
            }
            isFiltered = true;
        } else if (startDate) {
            periodLabel = `Mulai ${startDate}`;
            isFiltered = true;
        } else if (endDate) {
            periodLabel = `Hingga ${endDate}`;
            isFiltered = true;
        }

        if (tagEl) {
            tagEl.innerText = periodLabel;
            tagEl.className = isFiltered
                ? 'text-[10px] px-2.5 py-0.5 rounded-full font-bold bg-amber-100 text-amber-800'
                : 'text-[10px] px-2.5 py-0.5 rounded-full font-bold bg-emerald-100 text-emerald-800';
        }

        if (balDescEl) {
            balDescEl.innerText = isFiltered ? `Net Cashflow (${periodLabel})` : 'Net Cashflow Juli 2026 s/d Kini';
        }

        document.getElementById('eco-stat-income').innerText = 'Rp ' + Math.round(inc).toLocaleString('id-ID');
        document.getElementById('eco-stat-income-count').innerText = isFiltered
            ? `${sum.count_income || 0} Transaksi (${periodLabel})`
            : `${sum.count_income || 0} Transaksi Penjualan / Sewa (Kumulatif)`;

        document.getElementById('eco-stat-expense').innerText = 'Rp ' + Math.round(exp).toLocaleString('id-ID');
        document.getElementById('eco-stat-expense-count').innerText = isFiltered
            ? `${sum.count_expense || 0} Transaksi (${periodLabel})`
            : `${sum.count_expense || 0} Transaksi Operasional (Kumulatif)`;

        const balEl = document.getElementById('eco-stat-balance');
        balEl.innerText = 'Rp ' + Math.round(bal).toLocaleString('id-ID');
        if (bal < 0) {
            balEl.classList.remove('text-indigo-800');
            balEl.classList.add('text-rose-700');
        } else {
            balEl.classList.remove('text-rose-700');
            balEl.classList.add('text-indigo-800');
        }

        const pctEl = document.getElementById('eco-stat-pct-serapan');
        if (pctEl) {
            pctEl.innerText = `Serapan ${pct}% dari Plafon RKAS`;
        }

        // Render AI Analyst Briefing
        const statusBadge = document.getElementById('ai-eco-status-badge');
        const statusText = document.getElementById('ai-eco-status-text');
        if (statusBadge && statusText) {
            statusText.innerText = ai.status || 'SURPLUS SEHAT';
            if (ai.status_color === 'rose') {
                statusBadge.className = 'px-3 py-1 rounded-full text-xs font-bold bg-rose-100 text-rose-800 border border-rose-300 flex items-center gap-1.5 shadow-2xs';
            } else if (ai.status_color === 'amber') {
                statusBadge.className = 'px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-300 flex items-center gap-1.5 shadow-2xs';
            } else {
                statusBadge.className = 'px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-1.5 shadow-2xs';
            }
        }

        if (document.getElementById('ai-eco-margin')) {
            document.getElementById('ai-eco-margin').innerText = (ai.surplus_rate || 0) + '%';
        }
        if (document.getElementById('ai-eco-oer')) {
            document.getElementById('ai-eco-oer').innerText = (ai.burn_ratio || 0) + '%';
        }
        if (document.getElementById('ai-eco-top-rev')) {
            const revEl = document.getElementById('ai-eco-top-rev');
            revEl.innerText = ai.top_revenue_driver || 'Sewa Fasilitas';
            revEl.title = ai.top_revenue_driver || 'Sewa Fasilitas';
        }
        if (document.getElementById('ai-eco-top-cost')) {
            const costEl = document.getElementById('ai-eco-top-cost');
            costEl.innerText = ai.top_cost_center || 'PEMELIHARAAN';
            costEl.title = ai.top_cost_center || 'PEMELIHARAAN';
        }

        const insightsList = document.getElementById('ai-eco-insights-list');
        if (insightsList && ai.insights) {
            insightsList.innerHTML = ai.insights.map(txt => `
                <li class="flex items-start gap-2.5 text-xs text-slate-800 font-medium">
                    <i class="fa-solid fa-circle-check text-emerald-600 mt-0.5 shrink-0 text-sm"></i>
                    <span class="leading-relaxed">${txt}</span>
                </li>
            `).join('');
        }

        // Render 6 Control Bars
        const cats = stats.categories || [];
        const catContainer = document.getElementById('eco-categories-container');
        if (catContainer) {
            let html = '';
            cats.forEach(c => {
                let barColor = 'bg-emerald-500';
                if (c.persentase > 80) barColor = 'bg-rose-500';
                else if (c.persentase > 50) barColor = 'bg-amber-500';

                html += `
                <div class="bg-slate-50 border border-slate-200/80 rounded-xl p-3 flex flex-col justify-between">
                    <div>
                        <div class="text-[10px] font-bold text-slate-400">${c.code}</div>
                        <div class="text-xs font-bold text-slate-700 truncate" title="${c.name}">${c.name}</div>
                        <div class="text-xs font-bold text-slate-800 mt-1">Rp ${Math.round(c.realisasi).toLocaleString('id-ID')}</div>
                        <div class="text-[10px] text-slate-500">Plafon: Rp ${(c.anggaran/1000000).toFixed(1)}M</div>
                    </div>
                    <div class="mt-2.5">
                        <div class="flex items-center justify-between text-[10px] mb-1">
                            <span class="text-slate-400">${c.transaksi} Trx</span>
                            <span class="font-bold text-slate-700">${c.persentase}%</span>
                        </div>
                        <div class="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
                            <div class="${barColor} h-1.5 rounded-full" style="width: ${Math.min(c.persentase, 100)}%"></div>
                        </div>
                    </div>
                </div>`;
            });
            catContainer.innerHTML = html;
        }
    }

    function renderEcoCharts(stats) {
        if (typeof Chart === 'undefined') {
            console.warn('Chart.js belum siap.');
            return;
        }

        // ----------------------------------------------------
        // GRAFIK 1: Tren Arus Kas Bulanan (Bar Ganda + Line Net)
        // ----------------------------------------------------
        const trendEl = document.getElementById('chart-eco-monthly-trend');
        if (trendEl) {
            if (window.ecoChartTrend instanceof Chart) {
                window.ecoChartTrend.destroy();
            }

            const trends = stats.monthly_trends || [];
            const labels = trends.map(t => t.month);
            const incomes = trends.map(t => t.income);
            const expenses = trends.map(t => t.expense);
            const nets = trends.map(t => t.net);

            window.ecoChartTrend = new Chart(trendEl, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Kas Masuk (Omset)',
                            data: incomes,
                            backgroundColor: 'rgba(16, 185, 129, 0.85)',
                            borderColor: '#059669',
                            borderWidth: 1.5,
                            borderRadius: 6,
                            order: 2
                        },
                        {
                            label: 'Kas Keluar (Belanja)',
                            data: expenses,
                            backgroundColor: 'rgba(244, 63, 94, 0.85)',
                            borderColor: '#e11d48',
                            borderWidth: 1.5,
                            borderRadius: 6,
                            order: 3
                        },
                        {
                            label: 'Saldo Bersih',
                            data: nets,
                            type: 'line',
                            borderColor: '#4f46e5',
                            backgroundColor: '#4f46e5',
                            pointBackgroundColor: '#4f46e5',
                            pointRadius: 4,
                            pointHoverRadius: 6,
                            borderWidth: 2.5,
                            tension: 0.25,
                            order: 1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: function(ctx) {
                                    return ctx.dataset.label + ': Rp ' + Math.round(ctx.parsed.y).toLocaleString('id-ID');
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(val) {
                                    return (val / 1000000).toFixed(1) + 'M';
                                },
                                font: { size: 10 }
                            },
                            grid: { color: 'rgba(226, 232, 240, 0.6)' }
                        },
                        x: {
                            ticks: { font: { size: 11, weight: '600' } },
                            grid: { display: false }
                        }
                    }
                }
            });
        }

        // ----------------------------------------------------
        // GRAFIK 2: Komposisi Sumber Pendapatan (Donut Chart)
        // ----------------------------------------------------
        const incomeEl = document.getElementById('chart-eco-income-donut');
        if (incomeEl) {
            if (window.ecoChartIncome instanceof Chart) {
                window.ecoChartIncome.destroy();
            }

            const incData = stats.income_breakdown || [];
            const top5 = incData.slice(0, 5);
            const otherSum = incData.slice(5).reduce((acc, curr) => acc + curr.amount, 0);
            if (otherSum > 0) {
                top5.push({ category: 'Lainnya', amount: otherSum, percentage: 0 });
            }

            const incLabels = top5.map(d => d.category);
            const incValues = top5.map(d => d.amount);
            const palette = ['#059669', '#0d9488', '#0284c7', '#6366f1', '#eab308', '#94a3b8'];

            window.ecoChartIncome = new Chart(incomeEl, {
                type: 'doughnut',
                data: {
                    labels: incLabels,
                    datasets: [{
                        data: incValues,
                        backgroundColor: palette.slice(0, incLabels.length),
                        borderWidth: 2,
                        borderColor: '#ffffff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: function(ctx) {
                                    const val = ctx.parsed || 0;
                                    const total = incValues.reduce((a, b) => a + b, 0);
                                    const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
                                    return ctx.label + ': Rp ' + Math.round(val).toLocaleString('id-ID') + ' (' + pct + '%)';
                                }
                            }
                        }
                    },
                    cutout: '65%'
                }
            });

            // Update Donut Legend HTML
            const legendEl = document.getElementById('eco-donut-legend');
            if (legendEl) {
                legendEl.innerHTML = top5.map((item, idx) => `
                    <div class="flex items-center gap-1.5 truncate">
                        <span class="w-2.5 h-2.5 rounded-full inline-block shrink-0" style="background-color: ${palette[idx] || '#94a3b8'}"></span>
                        <span class="truncate" title="${item.category}">${item.category}:</span>
                        <span class="font-bold text-slate-800 shrink-0">Rp ${(item.amount/1000000).toFixed(1)}M</span>
                    </div>
                `).join('');
            }
        }

        // ----------------------------------------------------
        // GRAFIK 3: Evaluasi Realisasi vs Plafon 6 Pos (Horizontal Bar)
        // ----------------------------------------------------
        const budgetEl = document.getElementById('chart-eco-budget-bars');
        if (budgetEl) {
            if (window.ecoChartBudget instanceof Chart) {
                window.ecoChartBudget.destroy();
            }

            const cats = stats.categories || [];
            const bLabels = cats.map(c => c.name.replace('OPERASIONAL ', ''));
            const bPlafon = cats.map(c => c.anggaran);
            const bReal = cats.map(c => c.realisasi);

            window.ecoChartBudget = new Chart(budgetEl, {
                type: 'bar',
                data: {
                    labels: bLabels,
                    datasets: [
                        {
                            label: 'Plafon RKAS',
                            data: bPlafon,
                            backgroundColor: 'rgba(203, 213, 225, 0.5)',
                            borderColor: '#94a3b8',
                            borderWidth: 1,
                            borderRadius: 4
                        },
                        {
                            label: 'Realisasi Belanja',
                            data: bReal,
                            backgroundColor: 'rgba(147, 51, 234, 0.85)',
                            borderColor: '#7e22ce',
                            borderWidth: 1.5,
                            borderRadius: 4
                        }
                    ]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: { boxWidth: 12, font: { size: 10 } }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(ctx) {
                                    return ctx.dataset.label + ': Rp ' + Math.round(ctx.parsed.x).toLocaleString('id-ID');
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            ticks: {
                                callback: function(val) { return (val / 1000000).toFixed(0) + 'M'; },
                                font: { size: 10 }
                            },
                            grid: { color: 'rgba(226, 232, 240, 0.6)' }
                        },
                        y: {
                            ticks: { font: { size: 10, weight: '500' } },
                            grid: { display: false }
                        }
                    }
                }
            });
        }

        // ----------------------------------------------------
        // GRAFIK 4: Top 8 Item Beban Pengeluaran Terbesar (Horizontal Bar)
        // ----------------------------------------------------
        const topExpEl = document.getElementById('chart-eco-top-expense');
        if (topExpEl) {
            if (window.ecoChartTopExp instanceof Chart) {
                window.ecoChartTopExp.destroy();
            }

            const items = stats.top_expense_items || [];
            const expLabels = items.map(i => i.item.length > 20 ? i.item.substring(0, 18) + '...' : i.item);
            const expValues = items.map(i => i.amount);

            window.ecoChartTopExp = new Chart(topExpEl, {
                type: 'bar',
                data: {
                    labels: expLabels,
                    datasets: [{
                        label: 'Pengeluaran',
                        data: expValues,
                        backgroundColor: 'rgba(225, 29, 72, 0.85)',
                        borderColor: '#be123c',
                        borderWidth: 1.5,
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
                                label: function(ctx) {
                                    return 'Total: Rp ' + Math.round(ctx.parsed.x).toLocaleString('id-ID');
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            ticks: {
                                callback: function(val) { return (val / 1000000).toFixed(1) + 'M'; },
                                font: { size: 10 }
                            },
                            grid: { color: 'rgba(226, 232, 240, 0.6)' }
                        },
                        y: {
                            ticks: { font: { size: 10, weight: '500' } },
                            grid: { display: false }
                        }
                    }
                }
            });
        }
    }

    function setEcoTypeFilter(type) {
        G_ECO_TYPE_FILTER = type;
        const bAll = document.getElementById('btn-eco-type-all');
        const bInc = document.getElementById('btn-eco-type-income');
        const bExp = document.getElementById('btn-eco-type-expense');

        if (bAll) bAll.className = 'px-3 py-1.5 rounded-lg text-slate-600 hover:text-slate-800 transition';
        if (bInc) bInc.className = 'px-3 py-1.5 rounded-lg text-slate-600 hover:text-emerald-700 transition flex items-center gap-1.5';
        if (bExp) bExp.className = 'px-3 py-1.5 rounded-lg text-slate-600 hover:text-rose-700 transition flex items-center gap-1.5';

        if (type === 'INCOME') {
            if (bInc) bInc.className = 'px-3 py-1.5 rounded-lg bg-emerald-600 text-white shadow-xs font-bold transition flex items-center gap-1.5';
        } else if (type === 'EXPENSE') {
            if (bExp) bExp.className = 'px-3 py-1.5 rounded-lg bg-rose-600 text-white shadow-xs font-bold transition flex items-center gap-1.5';
        } else {
            if (bAll) bAll.className = 'px-3 py-1.5 rounded-lg bg-white text-slate-800 shadow-xs font-bold transition';
        }

        filterEcoData();
    }

    function debounceEcoSearch() {
        if (G_ECO_SEARCH_TIMER) clearTimeout(G_ECO_SEARCH_TIMER);
        G_ECO_SEARCH_TIMER = setTimeout(() => {
            filterEcoData();
        }, 250);
    }

    let G_ECO_PAGE = 1;
    let G_ECO_PAGE_SIZE = 25;
    let G_ECO_SORT = 'date_desc';
    let G_ECO_FILTERED_CACHE = [];

    function onEcoTableFilterChange() {
        G_ECO_PAGE = 1;
        filterEcoData();
    }

    function onEcoPageSizeChange() {
        const ps = document.getElementById('eco-table-pagesize') ? document.getElementById('eco-table-pagesize').value : '25';
        G_ECO_PAGE_SIZE = ps === 'all' ? 999999 : parseInt(ps, 10);
        G_ECO_PAGE = 1;
        filterEcoData();
    }

    function resetEcoTableFilters() {
        if (document.getElementById('eco-table-quick-search')) document.getElementById('eco-table-quick-search').value = '';
        if (document.getElementById('eco-table-filter-type')) document.getElementById('eco-table-filter-type').value = '';
        if (document.getElementById('eco-table-filter-cat')) document.getElementById('eco-table-filter-cat').value = '';
        if (document.getElementById('eco-table-filter-proof')) document.getElementById('eco-table-filter-proof').value = '';
        if (document.getElementById('eco-table-filter-nominal')) document.getElementById('eco-table-filter-nominal').value = '';
        if (document.getElementById('eco-table-sort')) document.getElementById('eco-table-sort').value = 'date_desc';
        if (document.getElementById('eco-table-pagesize')) document.getElementById('eco-table-pagesize').value = '25';
        G_ECO_PAGE = 1;
        G_ECO_PAGE_SIZE = 25;
        G_ECO_SORT = 'date_desc';
        filterEcoData();
    }

    function gotoEcoPage(pageNum) {
        G_ECO_PAGE = pageNum;
        renderEcoPaginatedTable();
    }

    function filterEcoData() {
        const topCat = document.getElementById('filter-eco-category') ? document.getElementById('filter-eco-category').value.toLowerCase().trim() : '';
        const topSearch = document.getElementById('search-eco-trx') ? document.getElementById('search-eco-trx').value.toLowerCase().trim() : '';

        const tblSearch = document.getElementById('eco-table-quick-search') ? document.getElementById('eco-table-quick-search').value.toLowerCase().trim() : '';
        const tblType = document.getElementById('eco-table-filter-type') ? document.getElementById('eco-table-filter-type').value.trim() : '';
        const tblCat = document.getElementById('eco-table-filter-cat') ? document.getElementById('eco-table-filter-cat').value.toLowerCase().trim() : '';
        const tblProof = document.getElementById('eco-table-filter-proof') ? document.getElementById('eco-table-filter-proof').value.trim() : '';
        const tblNominal = document.getElementById('eco-table-filter-nominal') ? document.getElementById('eco-table-filter-nominal').value.trim() : '';
        const sortMode = document.getElementById('eco-table-sort') ? document.getElementById('eco-table-sort').value : 'date_desc';

        const effectiveType = tblType || G_ECO_TYPE_FILTER;

        const filtered = G_ECO_DATA.filter(item => {
            if (effectiveType && item.trx_type !== effectiveType) {
                return false;
            }

            if (topCat) {
                const itemCat = (item.main_category || '').toLowerCase();
                const itemCoa = (item.coa_name || '').toLowerCase();
                if (!itemCat.includes(topCat) && !itemCoa.includes(topCat)) {
                    return false;
                }
            }

            if (tblCat) {
                const combCat = ((item.main_category || '') + ' ' + (item.coa_name || '') + ' ' + (item.coa_code || '')).toLowerCase();
                if (!combCat.includes(tblCat)) {
                    return false;
                }
            }

            if (tblProof === 'with_proof' && !item.drive_file_url) return false;
            if (tblProof === 'no_proof' && item.drive_file_url) return false;

            const amt = item.amount || 0;
            if (tblNominal === 'gt_1m' && amt <= 1000000) return false;
            if (tblNominal === '100k_1m' && (amt < 100000 || amt > 1000000)) return false;
            if (tblNominal === 'lt_100k' && amt >= 100000) return false;

            const combined = [
                item.description, item.buyer_or_vendor, item.coa_name, item.main_category, item.id
            ].join(' ').toLowerCase();

            if (topSearch && !combined.includes(topSearch)) return false;
            if (tblSearch && !combined.includes(tblSearch)) return false;

            return true;
        });

        filtered.sort((a, b) => {
            if (sortMode === 'date_asc') return (a.transaction_date || '').localeCompare(b.transaction_date || '');
            if (sortMode === 'amount_desc') return (b.amount || 0) - (a.amount || 0);
            if (sortMode === 'amount_asc') return (a.amount || 0) - (b.amount || 0);
            return (b.transaction_date || '').localeCompare(a.transaction_date || '');
        });

        G_ECO_FILTERED_CACHE = filtered;
        renderEcoPaginatedTable();
    }

    function renderEcoPaginatedTable() {
        const data = G_ECO_FILTERED_CACHE;
        const tbody = document.getElementById('eco-table-body');
        const lblCount = document.getElementById('lbl-table-count');
        const lblTotal = document.getElementById('lbl-table-total');
        const lblCntAll = document.getElementById('lbl-cnt-all');
        const paginationInfo = document.getElementById('eco-pagination-info');
        const paginationBtns = document.getElementById('eco-pagination-buttons');

        if (lblCntAll) lblCntAll.innerText = G_ECO_DATA.length;
        if (lblCount) lblCount.innerText = data.length;

        let totalAmountFiltered = 0;
        data.forEach(x => { totalAmountFiltered += (x.amount || 0); });
        if (lblTotal) lblTotal.innerText = 'Rp ' + Math.round(totalAmountFiltered).toLocaleString('id-ID');

        if (!tbody) return;

        if (data.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center py-8 text-slate-400">
                        <i class="fa-solid fa-folder-open text-2xl mb-1 text-slate-300"></i>
                        <div>Tidak ada transaksi yang cocok dengan filter yang dipilih.</div>
                    </td>
                </tr>`;
            if (paginationInfo) paginationInfo.innerText = 'Menampilkan 0 dari 0 transaksi';
            if (paginationBtns) paginationBtns.innerHTML = '';
            return;
        }

        const totalRows = data.length;
        const pageSize = G_ECO_PAGE_SIZE;
        const totalPages = Math.ceil(totalRows / pageSize) || 1;
        if (G_ECO_PAGE > totalPages) G_ECO_PAGE = totalPages;
        if (G_ECO_PAGE < 1) G_ECO_PAGE = 1;

        const startIndex = (G_ECO_PAGE - 1) * pageSize;
        const endIndex = Math.min(startIndex + pageSize, totalRows);
        const pagedData = data.slice(startIndex, endIndex);

        if (paginationInfo) {
            paginationInfo.innerText = `Menampilkan ${startIndex + 1} - ${endIndex} dari ${totalRows} transaksi`;
        }

        if (paginationBtns) {
            let btnsHtml = '';
            if (G_ECO_PAGE > 1) {
                btnsHtml += `<button type="button" onclick="gotoEcoPage(${G_ECO_PAGE - 1})" class="px-2.5 py-1 bg-white hover:bg-slate-100 border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 transition cursor-pointer flex items-center gap-1"><i class="fa-solid fa-chevron-left text-[10px]"></i> Sebelumnya</button>`;
            } else {
                btnsHtml += `<button type="button" disabled class="px-2.5 py-1 bg-slate-50 border border-slate-100 rounded-lg text-xs font-semibold text-slate-300 cursor-not-allowed">Sebelumnya</button>`;
            }

            btnsHtml += `<span class="px-3 py-1 font-bold text-xs text-slate-700 bg-white border border-slate-200 rounded-lg">${G_ECO_PAGE} / ${totalPages}</span>`;

            if (G_ECO_PAGE < totalPages) {
                btnsHtml += `<button type="button" onclick="gotoEcoPage(${G_ECO_PAGE + 1})" class="px-2.5 py-1 bg-white hover:bg-slate-100 border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 transition cursor-pointer flex items-center gap-1">Berikutnya <i class="fa-solid fa-chevron-right text-[10px]"></i></button>`;
            } else {
                btnsHtml += `<button type="button" disabled class="px-2.5 py-1 bg-slate-50 border border-slate-100 rounded-lg text-xs font-semibold text-slate-300 cursor-not-allowed">Berikutnya</button>`;
            }
            paginationBtns.innerHTML = btnsHtml;
        }

        let html = '';
        pagedData.forEach(item => {
            const isInc = item.trx_type === 'INCOME';

            const badgeType = isInc
                ? `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">
                     <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>MASUK
                   </span>`
                : `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800">
                     <span class="w-1.5 h-1.5 rounded-full bg-rose-500"></span>KELUAR
                   </span>`;

            const imgBtn = item.drive_file_url
                ? `<button type="button" onclick="showEcoImage('${item.drive_file_url}', '${encodeURIComponent(item.description)}')" class="px-2 py-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 rounded-lg text-xs font-semibold transition cursor-pointer flex items-center gap-1 mx-auto" title="Lihat Bukti Foto">
                     <i class="fa-solid fa-receipt"></i><span>Bukti</span>
                   </button>`
                : `<span class="text-slate-300 text-[11px]">-</span>`;

            html += `
            <tr class="hover:bg-slate-50/80 transition">
                <td class="py-2.5 px-4 font-mono">
                    <div class="font-bold text-slate-800">${item.transaction_date}</div>
                    <div class="text-[10px] text-slate-400">${item.id}</div>
                </td>
                <td class="py-2.5 px-3">
                    <div class="flex items-center gap-1.5 mb-0.5">${badgeType}</div>
                    <div class="text-[11px] font-semibold text-slate-700 truncate max-w-[150px]" title="${item.main_category || item.coa_name || '-'}">
                        ${item.main_category || item.coa_name || '-'}
                    </div>
                </td>
                <td class="py-2.5 px-4">
                    <div class="font-medium text-slate-800 text-xs">${item.description || '-'}</div>
                    <div class="text-[10px] text-slate-400 flex items-center gap-2 mt-0.5">
                        <span>Qty: ${item.qty || 1} ${item.unit || ''}</span>
                        ${item.coa_code ? `<span class="bg-slate-100 px-1 rounded text-slate-500 font-mono">${item.coa_code}</span>` : ''}
                    </div>
                </td>
                <td class="py-2.5 px-3 text-slate-600 font-medium">
                    ${item.buyer_or_vendor || '-'}
                </td>
                <td class="py-2.5 px-3 text-right font-mono font-bold ${isInc ? 'text-emerald-700' : 'text-slate-800'}">
                    ${isInc ? '+' : '-'}Rp ${Math.round(item.amount).toLocaleString('id-ID')}
                </td>
                <td class="py-2.5 px-3 text-center">
                    <span class="px-2 py-0.5 rounded text-[10px] font-semibold ${item.payment_method === 'Cash' ? 'bg-amber-50 text-amber-800 border border-amber-200/60' : 'bg-blue-50 text-blue-800 border border-blue-200/60'}">
                        ${item.payment_method || 'Cash'}
                    </span>
                </td>
                <td class="py-2.5 px-3 text-center">
                    ${imgBtn}
                </td>
                <td class="py-2.5 px-3 text-center">
                    <div class="flex items-center justify-center gap-1">
                        <button type="button" onclick="editEcoTransaction('${item.id}')" class="p-1.5 text-slate-400 hover:text-indigo-600 transition cursor-pointer" title="Edit Transaksi">
                            <i class="fa-solid fa-pen-to-square"></i>
                        </button>
                        <button type="button" onclick="deleteEcoTransaction('${item.id}')" class="p-1.5 text-slate-400 hover:text-rose-600 transition cursor-pointer" title="Hapus Transaksi">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>`;
        });

        tbody.innerHTML = html;
    }

    function openCreateEcoModal(type) {
        toggleCreateType(type || 'EXPENSE');
        const todayStr = new Date().toISOString().split('T')[0];
        document.getElementById('create-eco-date').value = todayStr;
        document.getElementById('create-eco-amount').value = '';
        document.getElementById('create-eco-pihak').value = '';
        document.getElementById('create-eco-desc').value = '';
        document.getElementById('create-eco-method').value = 'Cash';
        toggleModal('modal-eco-create');
    }

    function toggleCreateType(type) {
        document.getElementById('create-eco-type').value = type;
        const bExp = document.getElementById('btn-create-type-expense');
        const bInc = document.getElementById('btn-create-type-income');
        const wrapCoa = document.getElementById('wrap-create-coa');
        const wrapIncCat = document.getElementById('wrap-create-income-cat');
        const lblPihak = document.getElementById('lbl-create-pihak');

        if (type === 'INCOME') {
            bInc.className = 'py-2 px-3 rounded-xl border text-xs font-bold transition flex items-center justify-center gap-1.5 border-emerald-500 bg-emerald-50 text-emerald-800';
            bExp.className = 'py-2 px-3 rounded-xl border text-xs font-bold transition flex items-center justify-center gap-1.5 border-slate-200 bg-white text-slate-600 hover:bg-slate-50';
            wrapCoa.classList.add('hidden');
            wrapIncCat.classList.remove('hidden');
            lblPihak.innerText = 'Nama Pembeli / Penyewa Fasilitas';
            document.getElementById('create-eco-modal-title').innerText = 'Catat Kas Masuk (Omset)';
            document.getElementById('create-eco-modal-icon').className = 'fa-solid fa-hand-holding-dollar';
        } else {
            bExp.className = 'py-2 px-3 rounded-xl border text-xs font-bold transition flex items-center justify-center gap-1.5 border-rose-500 bg-rose-50 text-rose-800';
            bInc.className = 'py-2 px-3 rounded-xl border text-xs font-bold transition flex items-center justify-center gap-1.5 border-slate-200 bg-white text-slate-600 hover:bg-slate-50';
            wrapCoa.classList.remove('hidden');
            wrapIncCat.classList.add('hidden');
            lblPihak.innerText = 'Nama Toko / Penjual / Mitra';
            document.getElementById('create-eco-modal-title').innerText = 'Catat Kas Keluar (Belanja Operasional)';
            document.getElementById('create-eco-modal-icon').className = 'fa-solid fa-receipt';
        }
    }

    async function submitCreateEco(event) {
        event.preventDefault();
        const type = document.getElementById('create-eco-type').value;
        const btn = document.getElementById('btn-save-create-eco');
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Menyimpan...';

        try {
            const isInc = type === 'INCOME';
            const payload = {
                trx_type: type,
                transaction_date: document.getElementById('create-eco-date').value,
                amount: parseFloat(document.getElementById('create-eco-amount').value || 0),
                buyer_or_vendor: document.getElementById('create-eco-pihak').value.trim(),
                description: document.getElementById('create-eco-desc').value.trim(),
                payment_method: document.getElementById('create-eco-method').value,
                coa_code: isInc ? '' : document.getElementById('create-eco-coa').value,
                main_category: isInc ? document.getElementById('create-eco-income-cat').value : ''
            };

            const res = await fetch('/api/eco/manual-create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();

            if (data.success) {
                toggleModal('modal-eco-create');
                await loadKeuanganEcopark();
            } else {
                alert('Gagal mencatat transaksi: ' + (data.error || 'Unknown error'));
            }
        } catch (e) {
            alert('Terjadi kesalahan jaringan: ' + e.message);
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="fa-solid fa-check"></i><span>Simpan Transaksi</span>';
        }
    }

    function editEcoTransaction(id) {
        const item = G_ECO_DATA.find(x => x.id === id);
        if (!item) return;

        document.getElementById('edit-eco-id').value = item.id;
        document.getElementById('edit-eco-type').value = item.trx_type;
        document.getElementById('edit-eco-id-display').innerText = `ID: ${item.id} (${item.month_period})`;

        const isInc = item.trx_type === 'INCOME';
        const typeBadge = document.getElementById('edit-eco-type-badge');
        typeBadge.innerHTML = isInc
            ? `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">KAS MASUK (OMSET)</span>`
            : `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800">KAS KELUAR (BELANJA)</span>`;

        document.getElementById('edit-eco-date').value = item.transaction_date;
        document.getElementById('edit-eco-amount').value = item.amount;
        document.getElementById('edit-eco-pihak').value = item.buyer_or_vendor || '';
        document.getElementById('edit-eco-desc').value = item.description || '';
        document.getElementById('edit-eco-method').value = item.payment_method || 'Cash';

        const wrapCoa = document.getElementById('wrap-edit-coa');
        const lblPihak = document.getElementById('lbl-edit-pihak');

        if (isInc) {
            if (wrapCoa) wrapCoa.classList.add('hidden');
            if (lblPihak) lblPihak.innerText = 'Nama Pembeli / Penyewa';
        } else {
            if (wrapCoa) wrapCoa.classList.remove('hidden');
            if (lblPihak) lblPihak.innerText = 'Nama Toko / Penjual';
            const selCoa = document.getElementById('edit-eco-coa');
            if (selCoa) selCoa.value = item.coa_code || '';
        }

        toggleModal('modal-eco-edit');
    }

    async function submitEditEco(event) {
        event.preventDefault();
        const id = document.getElementById('edit-eco-id').value;
        const btn = document.getElementById('btn-save-edit-eco');
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Menyimpan...';

        try {
            const isInc = document.getElementById('edit-eco-type').value === 'INCOME';
            const payload = {
                transaction_date: document.getElementById('edit-eco-date').value,
                amount: parseFloat(document.getElementById('edit-eco-amount').value || 0),
                buyer_or_vendor: document.getElementById('edit-eco-pihak').value.trim(),
                description: document.getElementById('edit-eco-desc').value.trim(),
                payment_method: document.getElementById('edit-eco-method').value,
                coa_code: isInc ? '' : document.getElementById('edit-eco-coa').value
            };

            const res = await fetch(`/api/eco/transactions/${id}/update`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();

            if (data.success) {
                toggleModal('modal-eco-edit');
                await loadKeuanganEcopark();
            } else {
                alert('Gagal menyimpan perubahan: ' + (data.error || 'Unknown error'));
            }
        } catch (e) {
            alert('Terjadi kesalahan: ' + e.message);
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="fa-solid fa-check"></i><span>Simpan Perubahan</span>';
        }
    }

    async function deleteEcoTransaction(id) {
        if (!confirm(`Apakah Mr Slam / Tim yakin ingin menghapus transaksi ${id}?`)) return;
        try {
            const res = await fetch(`/api/eco/transactions/${id}`, { method: 'DELETE' });
            const data = await res.json();
            if (data.success) {
                await loadKeuanganEcopark();
            } else {
                alert('Gagal menghapus: ' + data.error);
            }
        } catch (e) {
            alert('Kesalahan jaringan: ' + e.message);
        }
    }

    function deleteEcoTransactionCurrent() {
        const id = document.getElementById('edit-eco-id').value;
        if (id) {
            toggleModal('modal-eco-edit');
            deleteEcoTransaction(id);
        }
    }

    function showEcoImage(url, title) {
        document.getElementById('eco-image-title').innerText = decodeURIComponent(title);
        document.getElementById('eco-image-src').src = url;
        document.getElementById('eco-image-drive-link').href = url;
        toggleModal('modal-eco-image');
    }

    function exportEcoExcel() {
        const startDate = document.getElementById('filter-eco-start-date') ? document.getElementById('filter-eco-start-date').value : '';
        const endDate = document.getElementById('filter-eco-end-date') ? document.getElementById('filter-eco-end-date').value : '';
        let url = '/api/eco/export?1=1';
        if (startDate) url += '&start_date=' + encodeURIComponent(startDate);
        if (endDate) url += '&end_date=' + encodeURIComponent(endDate);
        if (G_ECO_TYPE_FILTER) url += '&type=' + encodeURIComponent(G_ECO_TYPE_FILTER);
        window.open(url, '_blank');
    }
    const exportEcoCSV = exportEcoExcel;

    function copyFormatText(elemId) {
        const el = document.getElementById(elemId);
        if (!el) return;
        navigator.clipboard.writeText(el.innerText).then(() => {
            alert('Template format berhasil disalin ke clipboard!');
        });
    }
</script>
"""
