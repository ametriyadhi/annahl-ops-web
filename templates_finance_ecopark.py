# -*- coding: utf-8 -*-
"""
templates_finance_ecopark.py - Komponen Tampilan HTML & JavaScript untuk Tab Keuangan Ciangsana Ecopark
An Nahl Islamic School - Dashboard Operasional note-umum
Mendukung Pencatatan Terpadu Kas Masuk (Omset) & Kas Keluar (Operasional FKP ECO 2026-2027),
Filter Cerdas, Modal Input/Edit Koreksi, Modal Panduan Format WA, dan Ekspor CSV.
"""

TAB_KEUANGAN_ECOPARK_HTML = """
<!-- TAB KEUANGAN TERPADU CIANGSANA ECOPARK -->
<div id="tab-keuangan-ecopark" class="tab-content hidden space-y-6">

    <!-- Header & Action Bar -->
    <div class="bg-white rounded-2xl shadow-xs border border-slate-200/80 p-4 sm:p-6 space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
            <div>
                <div class="flex items-center gap-2 flex-wrap">
                    <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 tracking-wider uppercase">Standar RKAS FKP ECO 2026–2027</span>
                    <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-blue-100 text-blue-700">Cashflow & Vision AI</span>
                    <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-100 text-amber-800">Google Drive Cloud</span>
                </div>
                <h2 class="text-base sm:text-xl font-bold text-slate-800 flex items-center gap-2 mt-1">
                    <i class="fa-solid fa-tree text-emerald-600"></i>
                    Buku Kas & Keuangan Terpadu Ciangsana Ecopark
                </h2>
                <p class="text-xs text-slate-500 mt-0.5">Pencatatan real-time Kas Masuk (Omset/Sewa/Panen) dan Kas Keluar (Operasional/Budidaya/Ternak/Sarpras) terintegrasi RKAS FKP ECO 2026–2027 & WhatsApp Bot.</p>
            </div>
            <div class="flex items-center gap-2 sm:gap-3 flex-wrap">
                <button type="button" onclick="loadKeuanganEcopark()" class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition flex items-center gap-1.5 cursor-pointer">
                    <i class="fa-solid fa-arrows-rotate"></i>
                    <span>Refresh</span>
                </button>
                <button type="button" onclick="openCreateEcoModal('EXPENSE')" class="px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold rounded-lg shadow-xs transition flex items-center gap-1.5 cursor-pointer">
                    <i class="fa-solid fa-receipt"></i>
                    <span>+ Catat Belanja</span>
                </button>
                <button type="button" onclick="openCreateEcoModal('INCOME')" class="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-lg shadow-xs transition flex items-center gap-1.5 cursor-pointer">
                    <i class="fa-solid fa-hand-holding-dollar"></i>
                    <span>+ Catat Pemasukan</span>
                </button>
                <button type="button" onclick="toggleModal('modal-eco-format')" class="px-3 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 text-xs font-semibold rounded-lg transition flex items-center gap-1.5 cursor-pointer">
                    <i class="fa-brands fa-whatsapp text-emerald-600"></i>
                    <span>Format Laporan WA</span>
                </button>
            </div>
        </div>

        <!-- 4 Summary Metric Cards -->
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 pt-1">
            <!-- 1. Total Pemasukan -->
            <div class="bg-emerald-50/50 border border-emerald-200/60 rounded-xl p-3.5">
                <div class="flex items-center justify-between text-emerald-700 text-xs font-medium">
                    <span>Kas Masuk (Omset)</span>
                    <i class="fa-solid fa-arrow-down-left text-emerald-600 text-sm"></i>
                </div>
                <div id="eco-stat-income" class="text-lg sm:text-2xl font-bold text-emerald-800 mt-1">Rp 0</div>
                <div id="eco-stat-income-count" class="text-[11px] text-emerald-600 font-medium mt-0.5">0 Transaksi Penjualan / Sewa</div>
            </div>

            <!-- 2. Total Pengeluaran -->
            <div class="bg-rose-50/50 border border-rose-200/60 rounded-xl p-3.5">
                <div class="flex items-center justify-between text-rose-700 text-xs font-medium">
                    <span>Kas Keluar (Belanja)</span>
                    <i class="fa-solid fa-arrow-up-right text-rose-600 text-sm"></i>
                </div>
                <div id="eco-stat-expense" class="text-lg sm:text-2xl font-bold text-rose-800 mt-1">Rp 0</div>
                <div id="eco-stat-expense-count" class="text-[11px] text-rose-600 font-medium mt-0.5">0 Transaksi Operasional</div>
            </div>

            <!-- 3. Saldo Kas Bersih -->
            <div class="bg-indigo-50/50 border border-indigo-200/60 rounded-xl p-3.5">
                <div class="flex items-center justify-between text-indigo-700 text-xs font-medium">
                    <span>Saldo Kas Bersih</span>
                    <i class="fa-solid fa-wallet text-indigo-600 text-sm"></i>
                </div>
                <div id="eco-stat-balance" class="text-lg sm:text-2xl font-bold text-indigo-800 mt-1">Rp 0</div>
                <div class="text-[11px] text-indigo-600 font-medium mt-0.5">Net Cashflow Juli 2026 s/d Kini</div>
            </div>

            <!-- 4. Kontrol Plafon RKAS -->
            <div class="bg-slate-50/70 border border-slate-200/70 rounded-xl p-3.5">
                <div class="flex items-center justify-between text-slate-600 text-xs font-medium">
                    <span>Plafon RKAS ECO</span>
                    <i class="fa-solid fa-chart-pie text-purple-600 text-sm"></i>
                </div>
                <div class="text-lg sm:text-2xl font-bold text-slate-800 mt-1">Rp 282.850.000</div>
                <div id="eco-stat-pct-serapan" class="text-[11px] text-purple-700 font-semibold mt-0.5">Serapan 0.0% dari Plafon</div>
            </div>
        </div>
    </div>

    <!-- 6 Pos Mata Anggaran Utama FKP ECO 2026-2027 (Control Bars) -->
    <div class="bg-white rounded-2xl shadow-xs border border-slate-200/80 p-4 sm:p-6 space-y-4">
        <div class="flex items-center justify-between">
            <h3 class="text-xs font-bold text-slate-600 uppercase tracking-wider flex items-center gap-2">
                <i class="fa-solid fa-layer-group text-slate-400"></i>
                Kontrol 6 Pos Plafon Anggaran Operasional Ecopark 2026–2027
            </h3>
            <span class="text-[11px] text-slate-400">Dasar Pengendalian Belanja Rutin</span>
        </div>
        <div id="eco-categories-container" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3">
            <div class="text-center py-4 text-xs text-slate-400 col-span-full">Memuat alokasi anggaran RKAS Ecopark...</div>
        </div>
    </div>

    <!-- Filter & Search Bar -->
    <div class="bg-white rounded-2xl shadow-xs border border-slate-200/80 p-4 space-y-3">
        <div class="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
            <!-- Filter Tipe Tab Switcher -->
            <div class="inline-flex p-1 bg-slate-100 rounded-xl gap-1 text-xs font-semibold self-start sm:self-auto">
                <button type="button" onclick="setEcoTypeFilter('')" id="btn-eco-type-all" class="px-3 py-1.5 rounded-lg bg-white text-slate-800 shadow-xs transition">Semua (892)</button>
                <button type="button" onclick="setEcoTypeFilter('INCOME')" id="btn-eco-type-income" class="px-3 py-1.5 rounded-lg text-slate-600 hover:text-emerald-700 transition flex items-center gap-1">
                    <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
                    <span>Kas Masuk (Omset)</span>
                </button>
                <button type="button" onclick="setEcoTypeFilter('EXPENSE')" id="btn-eco-type-expense" class="px-3 py-1.5 rounded-lg text-slate-600 hover:text-rose-700 transition flex items-center gap-1">
                    <span class="w-2 h-2 rounded-full bg-rose-500"></span>
                    <span>Kas Keluar (Belanja)</span>
                </button>
            </div>

            <!-- Filter Bulan, Kategori & Search -->
            <div class="flex items-center gap-2 flex-wrap flex-1 sm:justify-end">
                <select id="filter-eco-month" onchange="filterEcoData()" class="px-3 py-2 bg-slate-50 border border-slate-200 text-slate-700 text-xs rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-hidden">
                    <option value="">Semua Bulan (Mulai Juli 2026)</option>
                    <option value="Oktober 2026" selected>Oktober 2026</option>
                    <option value="September 2026">September 2026</option>
                    <option value="Agustus 2026">Agustus 2026</option>
                    <option value="Juli 2026">Juli 2026</option>
                </select>

                <select id="filter-eco-category" onchange="filterEcoData()" class="px-3 py-2 bg-slate-50 border border-slate-200 text-slate-700 text-xs rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-hidden">
                    <option value="">Semua Kategori / Pos</option>
                    <optgroup label="Pengeluaran (FKP ECO)">
                        <option value="OPERASIONAL BUDIDAYA">52111 Operasional Budidaya</option>
                        <option value="OPERASIONAL PETERNAKAN">52121 Operasional Peternakan</option>
                        <option value="PEMELIHARAAN">52131 Pemeliharaan</option>
                        <option value="OPERASIONAL KUNJUNGAN & EDUKASI">52132 Kunjungan & Edukasi</option>
                        <option value="MARKETING">52133 Marketing</option>
                        <option value="INVESTASI">52134 Investasi</option>
                    </optgroup>
                    <optgroup label="Pendapatan (Omset)">
                        <option value="Sewa Fasilitas">Sewa Fasilitas (Kolam/Lapangan/ISBI)</option>
                        <option value="Sayuran">Hasil Sayuran</option>
                        <option value="Telur">Hasil Telur</option>
                        <option value="Buah">Hasil Buah Sunnah & Lokal</option>
                        <option value="Kunjungan Edukasi">Kunjungan Edukasi & Outbound</option>
                    </optgroup>
                </select>

                <div class="relative flex-1 min-w-[180px] sm:max-w-xs">
                    <input type="text" id="search-eco-trx" onkeyup="debounceEcoSearch()" placeholder="Cari uraian, pembeli, toko..." class="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 text-slate-700 text-xs rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-hidden">
                    <i class="fa-solid fa-magnifying-glass absolute left-3 top-2.5 text-slate-400 text-xs"></i>
                </div>

                <button type="button" onclick="exportEcoCSV()" class="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl transition flex items-center gap-1.5 cursor-pointer">
                    <i class="fa-solid fa-file-excel text-emerald-600"></i>
                    <span>Ekspor CSV</span>
                </button>
            </div>
        </div>
    </div>

    <!-- Tabel Data Transaksi -->
    <div class="bg-white rounded-2xl shadow-xs border border-slate-200/80 overflow-hidden">
        <div class="overflow-x-auto">
            <table class="w-full text-left border-collapse min-w-[900px]">
                <thead>
                    <tr class="bg-slate-50/75 border-b border-slate-200/80 text-[11px] font-bold text-slate-600 uppercase tracking-wider">
                        <th class="py-3 px-4">Tipe & ID</th>
                        <th class="py-3 px-3">Tanggal</th>
                        <th class="py-3 px-3">Pihak Terkait</th>
                        <th class="py-3 px-4">Uraian / Deskripsi</th>
                        <th class="py-3 px-3">Pos Anggaran / Kategori</th>
                        <th class="py-3 px-4 text-right">Nominal (Rp)</th>
                        <th class="py-3 px-3 text-center">Metode</th>
                        <th class="py-3 px-3 text-center">Bukti</th>
                        <th class="py-3 px-4 text-center">Aksi</th>
                    </tr>
                </thead>
                <tbody id="eco-transactions-tbody" class="divide-y divide-slate-100 text-xs text-slate-700">
                    <tr>
                        <td colspan="9" class="py-8 text-center text-slate-400">
                            <i class="fa-solid fa-spinner fa-spin mr-2"></i>Memuat riwayat transaksi Ecopark...
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Table Footer / Counter -->
        <div class="p-4 border-t border-slate-100 bg-slate-50/50 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-500">
            <div id="eco-table-summary">Menampilkan 0 transaksi</div>
            <div class="flex items-center gap-2">
                <span class="text-[11px] text-slate-400">Data tercatat dari Juli 2026 s/d kini</span>
            </div>
        </div>
    </div>

</div>

<!-- ==================== MODAL CREATE TRANSAKSI MANUAL ==================== -->
<div id="modal-eco-create" class="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs hidden items-center justify-center p-4">
    <div class="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-lg overflow-hidden animate-in fade-in duration-150">
        <div class="px-6 py-4 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
            <h3 id="modal-eco-create-title" class="text-sm font-bold text-slate-800 flex items-center gap-2">
                <i class="fa-solid fa-plus-circle text-emerald-600"></i>
                <span>Catat Transaksi Baru Ecopark</span>
            </h3>
            <button type="button" onclick="toggleModal('modal-eco-create')" class="text-slate-400 hover:text-slate-600 cursor-pointer text-lg">&times;</button>
        </div>
        <form id="form-eco-create" onsubmit="submitCreateEco(event)" class="p-6 space-y-4">
            <!-- Switcher Tipe -->
            <div class="grid grid-cols-2 gap-2 p-1 bg-slate-100 rounded-xl">
                <label class="flex items-center justify-center gap-2 py-2 text-xs font-bold rounded-lg cursor-pointer transition has-checked:bg-emerald-600 has-checked:text-white text-slate-600">
                    <input type="radio" name="create_trx_type" value="INCOME" onchange="toggleCreateType('INCOME')" class="hidden">
                    <i class="fa-solid fa-arrow-down-left"></i>
                    <span>Kas Masuk (Omset)</span>
                </label>
                <label class="flex items-center justify-center gap-2 py-2 text-xs font-bold rounded-lg cursor-pointer transition has-checked:bg-rose-600 has-checked:text-white text-slate-600">
                    <input type="radio" name="create_trx_type" value="EXPENSE" onchange="toggleCreateType('EXPENSE')" checked class="hidden">
                    <i class="fa-solid fa-arrow-up-right"></i>
                    <span>Kas Keluar (Belanja)</span>
                </label>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                    <label class="block text-xs font-bold text-slate-700 mb-1">Tanggal Transaksi</label>
                    <input type="date" id="create-eco-date" required class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-hidden">
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-700 mb-1">Nominal (Rp)</label>
                    <input type="number" id="create-eco-amount" min="1" step="1" required placeholder="Contoh: 150000" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-hidden font-mono">
                </div>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                    <label id="lbl-create-pihak" class="block text-xs font-bold text-slate-700 mb-1">Nama Toko / Penjual</label>
                    <input type="text" id="create-eco-pihak" required placeholder="Contoh: Toko Pakan Berkah" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-hidden">
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-700 mb-1">Metode Pembayaran</label>
                    <select id="create-eco-method" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-hidden">
                        <option value="Cash">Cash (Tunai)</option>
                        <option value="Transfer">Transfer Bank</option>
                        <option value="QRIS">QRIS</option>
                    </select>
                </div>
            </div>

            <div id="wrap-create-coa">
                <label class="block text-xs font-bold text-slate-700 mb-1">Pos Anggaran FKP ECO</label>
                <select id="create-eco-coa" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-hidden">
                    <option value="">-- Pilih Pos Anggaran FKP --</option>
                </select>
            </div>

            <div id="wrap-create-income-cat" class="hidden">
                <label class="block text-xs font-bold text-slate-700 mb-1">Kategori Pemasukan</label>
                <select id="create-eco-income-cat" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-hidden">
                    <option value="Sewa Fasilitas">Sewa Fasilitas (Kolam/Lapangan/ISBI/Camping)</option>
                    <option value="Sayuran">Hasil Sayuran Hidroponik & Kebun</option>
                    <option value="Telur">Hasil Telur Ayam & Bebek</option>
                    <option value="Buah">Hasil Buah Sunnah & Lokal</option>
                    <option value="Ternak">Hasil Peternakan</option>
                    <option value="Kunjungan Edukasi">Kunjungan Edukasi & Outbound</option>
                    <option value="Lain-lain">Lain-lain</option>
                </select>
            </div>

            <div>
                <label class="block text-xs font-bold text-slate-700 mb-1">Uraian / Deskripsi Barang / Layanan</label>
                <textarea id="create-eco-desc" rows="2" required placeholder="Contoh: Pembelian Pur GT 1 karung & dedak pakan ayam" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-hidden"></textarea>
            </div>

            <div class="pt-3 border-t border-slate-100 flex items-center justify-end gap-2">
                <button type="button" onclick="toggleModal('modal-eco-create')" class="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl transition cursor-pointer">Batal</button>
                <button type="submit" id="btn-save-create-eco" class="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-xl shadow-xs transition flex items-center gap-1.5 cursor-pointer">
                    <i class="fa-solid fa-check"></i>
                    <span>Simpan Transaksi</span>
                </button>
            </div>
        </form>
    </div>
</div>

<!-- ==================== MODAL EDIT TRANSAKSI ==================== -->
<div id="modal-eco-edit" class="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs hidden items-center justify-center p-4">
    <div class="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-lg overflow-hidden animate-in fade-in duration-150">
        <div class="px-6 py-4 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
            <h3 class="text-sm font-bold text-slate-800 flex items-center gap-2">
                <i class="fa-solid fa-pen-to-square text-emerald-600"></i>
                <span>Koreksi & Edit Transaksi Ecopark</span>
            </h3>
            <button type="button" onclick="toggleModal('modal-eco-edit')" class="text-slate-400 hover:text-slate-600 cursor-pointer text-lg">&times;</button>
        </div>
        <form id="form-eco-edit" onsubmit="submitEditEco(event)" class="p-6 space-y-4">
            <input type="hidden" id="edit-eco-id">
            <input type="hidden" id="edit-eco-type">

            <div class="p-3 bg-slate-50 border border-slate-200/80 rounded-xl flex items-center justify-between text-xs">
                <div>
                    <span class="text-slate-400">ID Transaksi:</span>
                    <span id="edit-eco-id-badge" class="font-mono font-bold text-slate-700 ml-1"></span>
                </div>
                <div id="edit-eco-type-badge"></div>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                    <label class="block text-xs font-bold text-slate-700 mb-1">Tanggal Transaksi</label>
                    <input type="date" id="edit-eco-date" required class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-hidden">
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-700 mb-1">Nominal (Rp)</label>
                    <input type="number" id="edit-eco-amount" min="1" step="1" required class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-hidden font-mono font-bold">
                </div>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                    <label id="lbl-edit-pihak" class="block text-xs font-bold text-slate-700 mb-1">Pihak (Toko / Pembeli)</label>
                    <input type="text" id="edit-eco-pihak" required class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-hidden">
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-700 mb-1">Metode Pembayaran</label>
                    <select id="edit-eco-method" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-hidden">
                        <option value="Cash">Cash (Tunai)</option>
                        <option value="Transfer">Transfer Bank</option>
                        <option value="QRIS">QRIS</option>
                    </select>
                </div>
            </div>

            <div id="wrap-edit-coa">
                <label class="block text-xs font-bold text-slate-700 mb-1">Pos Anggaran FKP ECO</label>
                <select id="edit-eco-coa" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-hidden">
                    <option value="">-- Pilih Pos Anggaran FKP --</option>
                </select>
            </div>

            <div>
                <label class="block text-xs font-bold text-slate-700 mb-1">Uraian / Deskripsi Barang / Layanan</label>
                <textarea id="edit-eco-desc" rows="2" required class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:ring-2 focus:ring-emerald-500 focus:outline-hidden"></textarea>
            </div>

            <div class="pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
                <button type="button" onclick="deleteEcoTransactionCurrent()" class="px-3 py-2 text-rose-600 hover:bg-rose-50 rounded-xl text-xs font-semibold transition cursor-pointer flex items-center gap-1">
                    <i class="fa-solid fa-trash"></i>
                    <span>Hapus</span>
                </button>
                <div class="flex items-center gap-2">
                    <button type="button" onclick="toggleModal('modal-eco-edit')" class="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl transition cursor-pointer">Batal</button>
                    <button type="submit" id="btn-save-edit-eco" class="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-xl shadow-xs transition flex items-center gap-1.5 cursor-pointer">
                        <i class="fa-solid fa-check"></i>
                        <span>Simpan Perubahan</span>
                    </button>
                </div>
            </div>
        </form>
    </div>
</div>

<!-- ==================== MODAL PANDUAN FORMAT WA ==================== -->
<div id="modal-eco-format" class="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs hidden items-center justify-center p-4">
    <div class="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-xl overflow-hidden animate-in fade-in duration-150">
        <div class="px-6 py-4 bg-emerald-700 text-white flex items-center justify-between">
            <h3 class="text-sm font-bold flex items-center gap-2">
                <i class="fa-brands fa-whatsapp text-emerald-300 text-base"></i>
                <span>Format Pelaporan WhatsApp Tim Ecopark</span>
            </h3>
            <button type="button" onclick="toggleModal('modal-eco-format')" class="text-emerald-200 hover:text-white cursor-pointer text-lg">&times;</button>
        </div>
        <div class="p-6 space-y-4 max-h-[80vh] overflow-y-auto text-xs text-slate-700">
            <p class="text-slate-600 leading-relaxed">
                Tim Ecopark (Pak Said Husaen, Mas Ekky, atau Mr Slam) dapat melaporkan transaksi langsung ke bot WhatsApp dengan 2 cara mudah:
            </p>

            <!-- Format 1: Belanja / Kas Keluar -->
            <div class="p-4 bg-rose-50/70 border border-rose-200 rounded-xl space-y-2">
                <div class="flex items-center justify-between text-rose-800 font-bold">
                    <span class="flex items-center gap-1.5"><i class="fa-solid fa-arrow-up-right text-rose-600"></i> Format 1: Belanja Operasional (Kas Keluar)</span>
                    <button type="button" onclick="copyFormatText('fmt-belanja')" class="text-[11px] px-2 py-0.5 bg-rose-200/80 hover:bg-rose-300 rounded font-semibold text-rose-900 cursor-pointer">Salin</button>
                </div>
                <pre id="fmt-belanja" class="p-3 bg-white border border-rose-200 rounded-lg text-[11px] font-mono text-slate-800 overflow-x-auto">#belanja_ecopark
Tanggal: Hari ini
Pos: Peternakan
Barang: Pur GT 1 Karung & Dedak
Nominal: 395000
Toko: Toko Pakan Barokah
Metode: Cash
Keterangan: Pakan ayam & bebek petelur</pre>
                <div class="text-[11px] text-rose-700 italic">
                    💡 <strong>Tips:</strong> Jika ada foto struk/nota belanja, cukup kirim foto ke bot dengan caption <code>#belanja_ecopark</code> (AI otomatis membaca rinciannya).
                </div>
            </div>

            <!-- Format 2: Pendapatan / Kas Masuk -->
            <div class="p-4 bg-emerald-50/70 border border-emerald-200 rounded-xl space-y-2">
                <div class="flex items-center justify-between text-emerald-800 font-bold">
                    <span class="flex items-center gap-1.5"><i class="fa-solid fa-arrow-down-left text-emerald-600"></i> Format 2: Pemasukan / Omset (Kas Masuk)</span>
                    <button type="button" onclick="copyFormatText('fmt-pemasukan')" class="text-[11px] px-2 py-0.5 bg-emerald-200/80 hover:bg-emerald-300 rounded font-semibold text-emerald-900 cursor-pointer">Salin</button>
                </div>
                <pre id="fmt-pemasukan" class="p-3 bg-white border border-emerald-200 rounded-lg text-[11px] font-mono text-slate-800 overflow-x-auto">#pemasukan_ecopark
Tanggal: Hari ini
Kategori: Sewa Fasilitas
Uraian: Sewa Kolam Renang (Fee Aquatic)
Pembeli: Siti Tri Hutami
Nominal: 500000
Metode: Transfer
Keterangan: Sesi terapi pekan ke-2</pre>
                <div class="text-[11px] text-emerald-700 italic">
                    💡 <strong>Tips:</strong> Jika ada bukti transfer m-banking, kirim foto ke bot dengan caption <code>#pemasukan_ecopark</code> (AI otomatis mencatatnya).
                </div>
            </div>

            <!-- Perintah Cek Status -->
            <div class="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1">
                <div class="font-bold text-slate-800">Perintah Pintas Bot WhatsApp:</div>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px]">
                    <div><code>#rekap_ecopark</code> : Cek saldo kas & omset bulan ini</div>
                    <div><code>#format_ecopark</code> : Kirim template format laporan</div>
                </div>
            </div>
        </div>
        <div class="px-6 py-3 bg-slate-50 border-t border-slate-100 text-right">
            <button type="button" onclick="toggleModal('modal-eco-format')" class="px-4 py-1.5 bg-slate-200 hover:bg-slate-300 text-slate-700 font-semibold rounded-xl transition cursor-pointer">Tutup</button>
        </div>
    </div>
</div>

<!-- ==================== MODAL PREVIEW GAMBAR BUKTI ==================== -->
<div id="modal-eco-image" class="fixed inset-0 z-50 bg-slate-900/80 backdrop-blur-xs hidden items-center justify-center p-4">
    <div class="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-2xl w-full overflow-hidden">
        <div class="p-4 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
            <h4 id="eco-image-title" class="text-xs font-bold text-slate-700 truncate">Bukti Transaksi Ecopark</h4>
            <button type="button" onclick="toggleModal('modal-eco-image')" class="text-slate-400 hover:text-slate-600 text-lg cursor-pointer">&times;</button>
        </div>
        <div class="p-4 text-center max-h-[75vh] overflow-y-auto">
            <img id="eco-image-src" src="" alt="Bukti" class="max-h-[65vh] mx-auto rounded-lg shadow-sm">
        </div>
        <div class="p-3 bg-slate-50 border-t border-slate-100 text-right">
            <a id="eco-image-drive-link" href="#" target="_blank" class="px-3 py-1.5 bg-emerald-600 text-white text-xs font-semibold rounded-lg hover:bg-emerald-700 inline-flex items-center gap-1.5">
                <i class="fa-brands fa-google-drive"></i>
                <span>Buka di Google Drive</span>
            </a>
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

            // 2. Fetch Stats
            const selMonth = document.getElementById('filter-eco-month') ? document.getElementById('filter-eco-month').value : '';
            const resStats = await fetch('/api/eco/stats' + (selMonth ? '?month=' + encodeURIComponent(selMonth) : ''));
            if (resStats.ok) {
                const sData = await resStats.json();
                if (sData.success) {
                    renderEcoStats(sData);
                }
            }

            // 3. Fetch Transactions
            let url = '/api/eco/transactions?limit=250';
            if (selMonth) url += '&month=' + encodeURIComponent(selMonth);
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

        document.getElementById('eco-stat-income').innerText = 'Rp ' + Math.round(inc).toLocaleString('id-ID');
        document.getElementById('eco-stat-income-count').innerText = (sum.count_income || 0) + ' Transaksi Penjualan / Sewa';

        document.getElementById('eco-stat-expense').innerText = 'Rp ' + Math.round(exp).toLocaleString('id-ID');
        document.getElementById('eco-stat-expense-count').innerText = (sum.count_expense || 0) + ' Transaksi Operasional';

        const balEl = document.getElementById('eco-stat-balance');
        balEl.innerText = 'Rp ' + Math.round(bal).toLocaleString('id-ID');
        if (bal < 0) {
            balEl.classList.remove('text-indigo-800');
            balEl.classList.add('text-rose-700');
        } else {
            balEl.classList.remove('text-rose-700');
            balEl.classList.add('text-indigo-800');
        }

        document.getElementById('eco-stat-pct-serapan').innerText = 'Serapan ' + pct + '% dari Plafon FKP';

        // Render 6 Pos Kategori FKP ECO
        const container = document.getElementById('eco-categories-container');
        if (!container) return;

        let html = '';
        (stats.categories || []).forEach(cat => {
            const real = cat.realisasi || 0;
            const bgt = cat.anggaran || 0;
            const pVal = cat.persentase || 0;

            let barColor = 'bg-emerald-500';
            if (pVal >= 100) barColor = 'bg-rose-500';
            else if (pVal >= 80) barColor = 'bg-amber-500';

            html += `
            <div class="border border-slate-200/80 rounded-xl p-3 bg-slate-50/50 hover:bg-slate-50 transition">
                <div class="text-[11px] font-bold text-slate-700 truncate" title="${cat.code} ${cat.name}">${cat.code} ${cat.name}</div>
                <div class="text-sm font-bold text-slate-800 mt-1">Rp ${Math.round(real).toLocaleString('id-ID')}</div>
                <div class="w-full bg-slate-200 rounded-full h-1.5 mt-2 overflow-hidden">
                    <div class="${barColor} h-1.5 rounded-full" style="width: ${Math.min(pVal, 100)}%"></div>
                </div>
                <div class="flex justify-between text-[10px] text-slate-400 mt-1">
                    <span>${pVal}%</span>
                    <span>Plafon: ${(bgt / 1000000).toFixed(1)}M</span>
                </div>
            </div>`;
        });
        container.innerHTML = html;
    }

    function setEcoTypeFilter(type) {
        G_ECO_TYPE_FILTER = type;
        const btnAll = document.getElementById('btn-eco-type-all');
        const btnInc = document.getElementById('btn-eco-type-income');
        const btnExp = document.getElementById('btn-eco-type-expense');

        [btnAll, btnInc, btnExp].forEach(b => {
            if (b) {
                b.classList.remove('bg-white', 'text-slate-800', 'shadow-xs', 'bg-emerald-600', 'bg-rose-600', 'text-white');
                b.classList.add('text-slate-600');
            }
        });

        if (type === '') {
            btnAll.classList.add('bg-white', 'text-slate-800', 'shadow-xs');
            btnAll.classList.remove('text-slate-600');
        } else if (type === 'INCOME') {
            btnInc.classList.add('bg-white', 'text-emerald-700', 'shadow-xs');
            btnInc.classList.remove('text-slate-600');
        } else if (type === 'EXPENSE') {
            btnExp.classList.add('bg-white', 'text-rose-700', 'shadow-xs');
            btnExp.classList.remove('text-slate-600');
        }

        filterEcoData();
    }

    function debounceEcoSearch() {
        clearTimeout(G_ECO_SEARCH_TIMER);
        G_ECO_SEARCH_TIMER = setTimeout(() => {
            filterEcoData();
        }, 250);
    }

    function filterEcoData() {
        const selMonth = document.getElementById('filter-eco-month') ? document.getElementById('filter-eco-month').value : '';
        const selCat = document.getElementById('filter-eco-category') ? document.getElementById('filter-eco-category').value : '';
        const search = document.getElementById('search-eco-trx') ? document.getElementById('search-eco-trx').value.toLowerCase().trim() : '';

        const filtered = G_ECO_DATA.filter(item => {
            if (G_ECO_TYPE_FILTER && item.trx_type !== G_ECO_TYPE_FILTER) return false;
            if (selMonth && item.month_period !== selMonth) return false;
            if (selCat) {
                if (item.main_category !== selCat && item.coa_name !== selCat) return false;
            }
            if (search) {
                const txt = (
                    (item.id || '') + ' ' +
                    (item.description || '') + ' ' +
                    (item.buyer_or_vendor || '') + ' ' +
                    (item.coa_name || '') + ' ' +
                    (item.main_category || '')
                ).toLowerCase();
                if (!txt.includes(search)) return false;
            }
            return true;
        });

        renderEcoTable(filtered);
    }

    function renderEcoTable(data) {
        const tbody = document.getElementById('eco-transactions-tbody');
        const summary = document.getElementById('eco-table-summary');
        if (!tbody) return;

        if (data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="9" class="py-8 text-center text-slate-400">Tidak ada transaksi yang cocok dengan filter.</td></tr>`;
            if (summary) summary.innerText = 'Menampilkan 0 transaksi';
            return;
        }

        let totalAmountFiltered = 0;
        let html = '';

        data.forEach(item => {
            const isInc = item.trx_type === 'INCOME';
            totalAmountFiltered += (item.amount || 0);

            const badgeType = isInc
                ? `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 whitespace-nowrap"><i class="fa-solid fa-arrow-down-left mr-1"></i>MASUK</span>`
                : `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800 whitespace-nowrap"><i class="fa-solid fa-arrow-up-right mr-1"></i>KELUAR</span>`;

            const driveBtn = item.drive_file_url
                ? `<button type="button" onclick="showEcoImage('${item.drive_file_url}', '${encodeURIComponent(item.description || 'Bukti Transaksi')}')" class="px-2 py-1 rounded-md bg-emerald-50 text-emerald-700 hover:bg-emerald-100 text-[11px] font-semibold transition" title="Lihat Bukti Foto"><i class="fa-solid fa-image"></i></button>`
                : `<span class="text-slate-300 text-[11px]">-</span>`;

            html += `
            <tr class="hover:bg-slate-50/70 transition">
                <td class="py-3 px-4">
                    <div class="flex items-center gap-1.5">
                        ${badgeType}
                    </div>
                    <div class="font-mono text-[10px] text-slate-400 mt-1">${item.id}</div>
                </td>
                <td class="py-3 px-3 whitespace-nowrap text-slate-600 font-medium">${item.transaction_date}</td>
                <td class="py-3 px-3">
                    <div class="font-semibold text-slate-800">${item.buyer_or_vendor || '-'}</div>
                    <div class="text-[10px] text-slate-400">${item.reporter_name || 'Tim Ecopark'}</div>
                </td>
                <td class="py-3 px-4 max-w-xs">
                    <div class="font-medium text-slate-800 line-clamp-2">${item.description || '-'}</div>
                    ${item.notes ? `<div class="text-[10px] text-slate-400 italic">${item.notes}</div>` : ''}
                </td>
                <td class="py-3 px-3">
                    <div class="font-semibold text-slate-700">${item.coa_name || item.main_category || '-'}</div>
                    ${item.coa_code ? `<span class="font-mono text-[10px] text-slate-400">${item.coa_code}</span>` : ''}
                </td>
                <td class="py-3 px-4 text-right font-mono font-bold whitespace-nowrap ${isInc ? 'text-emerald-700' : 'text-rose-700'}">
                    ${isInc ? '+' : '-'} Rp ${Math.round(item.amount || 0).toLocaleString('id-ID')}
                </td>
                <td class="py-3 px-3 text-center whitespace-nowrap">
                    <span class="px-2 py-0.5 rounded-md text-[10px] font-medium bg-slate-100 text-slate-600">${item.payment_method || 'Cash'}</span>
                </td>
                <td class="py-3 px-3 text-center whitespace-nowrap">
                    ${driveBtn}
                </td>
                <td class="py-3 px-4 text-center whitespace-nowrap">
                    <button type="button" onclick="editEcoTransaction('${item.id}')" class="p-1.5 text-slate-400 hover:text-emerald-600 rounded-lg hover:bg-slate-100 transition cursor-pointer" title="Edit Koreksi">
                        <i class="fa-solid fa-pen-to-square"></i>
                    </button>
                    <button type="button" onclick="deleteEcoTransaction('${item.id}')" class="p-1.5 text-slate-400 hover:text-rose-600 rounded-lg hover:bg-slate-100 transition cursor-pointer ml-1" title="Hapus">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </td>
            </tr>`;
        });

        tbody.innerHTML = html;
        if (summary) {
            summary.innerHTML = `Menampilkan <strong>${data.length}</strong> transaksi. Total Nominal: <strong class="text-slate-800">Rp ${Math.round(totalAmountFiltered).toLocaleString('id-ID')}</strong>`;
        }
    }

    function openCreateEcoModal(type) {
        const form = document.getElementById('form-eco-create');
        if (form) form.reset();

        document.getElementById('create-eco-date').value = new Date().toISOString().slice(0, 10);
        const radio = document.querySelector(`input[name="create_trx_type"][value="${type}"]`);
        if (radio) {
            radio.checked = true;
            toggleCreateType(type);
        }
        toggleModal('modal-eco-create');
    }

    function toggleCreateType(type) {
        const lblPihak = document.getElementById('lbl-create-pihak');
        const wrapCoa = document.getElementById('wrap-create-coa');
        const wrapIncomeCat = document.getElementById('wrap-create-income-cat');
        const title = document.getElementById('modal-eco-create-title');

        if (type === 'INCOME') {
            if (lblPihak) lblPihak.innerText = 'Nama Pembeli / Penyewa';
            if (wrapCoa) wrapCoa.classList.add('hidden');
            if (wrapIncomeCat) wrapIncomeCat.classList.remove('hidden');
            if (title) title.innerHTML = '<i class="fa-solid fa-hand-holding-dollar text-emerald-600"></i><span>Catat Kas Masuk (Omset Ecopark)</span>';
        } else {
            if (lblPihak) lblPihak.innerText = 'Nama Toko / Penjual';
            if (wrapCoa) wrapCoa.classList.remove('hidden');
            if (wrapIncomeCat) wrapIncomeCat.classList.add('hidden');
            if (title) title.innerHTML = '<i class="fa-solid fa-receipt text-rose-600"></i><span>Catat Kas Keluar (Belanja Ecopark)</span>';
        }
    }

    async function submitCreateEco(event) {
        event.preventDefault();
        const btn = document.getElementById('btn-save-create-eco');
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Menyimpan...';

        try {
            const trxType = document.querySelector('input[name="create_trx_type"]:checked').value;
            const payload = {
                trx_type: trxType,
                transaction_date: document.getElementById('create-eco-date').value,
                amount: parseFloat(document.getElementById('create-eco-amount').value),
                buyer_or_vendor: document.getElementById('create-eco-pihak').value,
                description: document.getElementById('create-eco-desc').value,
                payment_method: document.getElementById('create-eco-method').value,
                coa_code: trxType === 'EXPENSE' ? document.getElementById('create-eco-coa').value : '',
                main_category: trxType === 'INCOME' ? document.getElementById('create-eco-income-cat').value : ''
            };

            const res = await fetch('/api/eco/transactions/manual', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();

            if (data.success) {
                toggleModal('modal-eco-create');
                await loadKeuanganEcopark();
            } else {
                alert('Gagal menyimpan transaksi: ' + (data.error || data.message || 'Unknown error'));
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
        document.getElementById('edit-eco-id-badge').innerText = item.id;

        const typeBadge = document.getElementById('edit-eco-type-badge');
        const isInc = item.trx_type === 'INCOME';
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
                amount: parseFloat(document.getElementById('edit-eco-amount').value),
                buyer_or_vendor: document.getElementById('edit-eco-pihak').value,
                description: document.getElementById('edit-eco-desc').value,
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

    function exportEcoCSV() {
        const selMonth = document.getElementById('filter-eco-month') ? document.getElementById('filter-eco-month').value : '';
        let url = '/api/eco/export?1=1';
        if (selMonth) url += '&month=' + encodeURIComponent(selMonth);
        if (G_ECO_TYPE_FILTER) url += '&type=' + encodeURIComponent(G_ECO_TYPE_FILTER);
        window.open(url, '_blank');
    }

    function copyFormatText(elemId) {
        const el = document.getElementById(elemId);
        if (!el) return;
        navigator.clipboard.writeText(el.innerText).then(() => {
            alert('Template format berhasil disalin ke clipboard!');
        });
    }
</script>
"""
