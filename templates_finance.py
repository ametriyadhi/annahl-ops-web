# -*- coding: utf-8 -*-
"""
templates_finance.py - Komponen Tampilan HTML & JavaScript untuk Tab Keuangan & FKP GA
An Nahl Islamic School - Dashboard Operasional note-umum
Mendukung Fitur View, Edit Koreksi, Hapus, dan Filter Realisasi Anggaran.
"""

TAB_KEUANGAN_HTML = """
<!-- TAB KEUANGAN & FKP GA AN NAHL -->
<div id="tab-keuangan" class="tab-content hidden space-y-6">

    <!-- Header & Action Bar -->
    <div class="bg-white rounded-2xl shadow-xs border border-slate-200/80 p-4 sm:p-6 space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
            <div>
                <div class="flex items-center gap-2">
                    <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 tracking-wider uppercase">Standar FKP GA 2026–2027</span>
                    <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-blue-100 text-blue-700">Vision AI & Google Drive</span>
                </div>
                <h2 class="text-base sm:text-xl font-bold text-slate-800 flex items-center gap-2 mt-1">
                    <i class="fa-solid fa-file-invoice-dollar text-emerald-600"></i>
                    Buku Kas & Pengeluaran Bagian Umum (General Affairs)
                </h2>
                <p class="text-xs text-slate-500 mt-0.5">Pencatatan otomatis bukti transfer m-banking & nota belanja via WhatsApp Bot Bu Rinni & Mr Slam, terintegrasi arsip Google Drive dan kontrol plafon anggaran FKP.</p>
            </div>
            <div class="flex items-center gap-2 sm:gap-3 flex-wrap">
                <button type="button" onclick="loadKeuanganGA()" class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition flex items-center gap-1.5 cursor-pointer">
                    <i class="fa-solid fa-arrows-rotate"></i>
                    <span>Refresh</span>
                </button>
                <div class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-lg text-xs font-semibold">
                    <i class="fa-brands fa-whatsapp text-emerald-500 text-sm"></i>
                    <span>Japri Bot: 0858-8229-6329</span>
                </div>
            </div>
        </div>

        <!-- 4 Summary Metric Cards -->
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 pt-1">
            <div class="bg-slate-50/70 border border-slate-200/70 rounded-xl p-3.5">
                <div class="flex items-center justify-between text-slate-500 text-xs font-medium">
                    <span>Realisasi Belanja GA</span>
                    <i class="fa-solid fa-money-bill-wave text-emerald-500"></i>
                </div>
                <div id="stat-grand-total" class="text-lg sm:text-2xl font-bold text-slate-800 mt-1">Rp 0</div>
                <div class="text-[11px] text-slate-400 mt-0.5">Total pengeluaran tercatat</div>
            </div>

            <div class="bg-slate-50/70 border border-slate-200/70 rounded-xl p-3.5">
                <div class="flex items-center justify-between text-slate-500 text-xs font-medium">
                    <span>Bukti Transaksi</span>
                    <i class="fa-solid fa-receipt text-blue-500"></i>
                </div>
                <div id="stat-total-trx" class="text-lg sm:text-2xl font-bold text-slate-800 mt-1">0 Transaksi</div>
                <div class="text-[11px] text-slate-400 mt-0.5">Nota & transfer terurai AI</div>
            </div>

            <div class="bg-slate-50/70 border border-slate-200/70 rounded-xl p-3.5">
                <div class="flex items-center justify-between text-slate-500 text-xs font-medium">
                    <span>Plafon RKAS GA</span>
                    <i class="fa-solid fa-chart-pie text-purple-500"></i>
                </div>
                <div class="text-lg sm:text-2xl font-bold text-slate-800 mt-1">Rp 1.507.851.796</div>
                <div id="stat-pct-serapan" class="text-[11px] text-emerald-600 font-semibold mt-0.5">Serapan 0.0%</div>
            </div>

            <div class="bg-slate-50/70 border border-slate-200/70 rounded-xl p-3.5">
                <div class="flex items-center justify-between text-slate-500 text-xs font-medium">
                    <span>Status Penyimpanan</span>
                    <i class="fa-brands fa-google-drive text-amber-500"></i>
                </div>
                <div class="text-lg sm:text-2xl font-bold text-slate-800 mt-1">Google Drive</div>
                <div class="text-[11px] text-emerald-600 font-semibold mt-0.5">Server Disk: 0 Byte (Aman)</div>
            </div>
        </div>
    </div>

    <!-- 5 Pos Mata Anggaran Utama FKP (Control Bars) -->
    <div class="bg-white rounded-2xl shadow-xs border border-slate-200/80 p-4 sm:p-6 space-y-4">
        <h3 class="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2">
            <i class="fa-solid fa-layer-group text-slate-400"></i>
            Kontrol 5 Pos Plafon Anggaran FKP GA 2026–2027
        </h3>
        <div id="finance-categories-container" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
            <div class="text-center py-4 text-xs text-slate-400 col-span-full">Memuat data alokasi anggaran...</div>
        </div>
    </div>

    <!-- Filter & Search Bar -->
    <div class="bg-white rounded-2xl shadow-xs border border-slate-200/80 p-4 space-y-3">
        <div class="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
            <div class="flex items-center gap-2 flex-wrap flex-1">
                <select id="filter-finance-month" onchange="filterFinanceData()" class="px-3 py-2 bg-slate-50 border border-slate-200 text-slate-700 text-xs rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-hidden">
                    <option value="">Semua Periode Bulan</option>
                    <option value="Oktober 2026" selected>Oktober 2026</option>
                    <option value="November 2026">November 2026</option>
                    <option value="Desember 2026">Desember 2026</option>
                    <option value="September 2026">September 2026</option>
                    <option value="Agustus 2026">Agustus 2026</option>
                    <option value="Juli 2026">Juli 2026</option>
                </select>

                <select id="filter-finance-category" onchange="filterFinanceData()" class="px-3 py-2 bg-slate-50 border border-slate-200 text-slate-700 text-xs rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-hidden">
                    <option value="">Semua Kategori Pos</option>
                    <option value="PEMELIHARAAN & PERBAIKAN">Pemeliharaan & Perbaikan (51411)</option>
                    <option value="ADMINISTRASI DAN UMUM">Administrasi & Umum / Kas Kecil (51412)</option>
                    <option value="ENERGI & KOMUNIKASI">Energi & Komunikasi (51413)</option>
                    <option value="PERLENGKAPAN">Perlengkapan (51414)</option>
                    <option value="INVESTASI">Investasi Sarpras (51415)</option>
                </select>
            </div>

            <div class="relative w-full sm:w-64">
                <input type="text" id="filter-finance-search" oninput="filterFinanceData()" placeholder="Cari toko, uraian, ref..." class="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 text-slate-700 text-xs rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-hidden">
                <i class="fa-solid fa-magnifying-glass absolute left-3 top-2.5 text-slate-400 text-xs"></i>
            </div>
        </div>
    </div>

    <!-- Data Table Transaksi Pengeluaran GA -->
    <div class="bg-white rounded-2xl shadow-xs border border-slate-200/80 overflow-hidden">
        <div class="overflow-x-auto">
            <table class="w-full text-left border-collapse text-xs">
                <thead>
                    <tr class="bg-slate-50/80 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider text-[11px]">
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
            <p class="font-medium text-slate-600">Belum ada pengeluaran yang tercatat pada filter ini.</p>
            <p class="text-xs text-slate-400 mt-1">Bu Rinni atau Mr Slam cukup kirim foto bukti bayar/nota via WhatsApp Bot.</p>
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
                    <label class="block font-bold text-slate-700 mb-1">Nominal Riil (Rp)</label>
                    <input type="number" id="edit-exp-amount" min="0" step="1" required class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-hidden font-bold text-emerald-700">
                </div>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                    <label class="block font-bold text-slate-700 mb-1">Penerima / Toko / Vendor</label>
                    <input type="text" id="edit-exp-vendor" placeholder="Contoh: TB Sentosa Jaya" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-hidden">
                </div>
                <div>
                    <label class="block font-bold text-slate-700 mb-1">Bank / No. Rekening</label>
                    <input type="text" id="edit-exp-bank" placeholder="Contoh: BCA 1234567890" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-hidden">
                </div>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                    <label class="block font-bold text-slate-700 mb-1">No. Referensi / Nota</label>
                    <input type="text" id="edit-exp-ref" placeholder="Contoh: TRF-99821" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-hidden">
                </div>
                <div>
                    <label class="block font-bold text-slate-700 mb-1">Sumber Dana FKP</label>
                    <select id="edit-exp-fund" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-hidden">
                        <option value="1. APBS Unit">1. APBS Unit</option>
                        <option value="2. SPP">2. SPP</option>
                        <option value="3. Lainnya">3. Lainnya</option>
                    </select>
                </div>
                <div>
                    <label class="block font-bold text-slate-700 mb-1">Unit Sasaran</label>
                    <select id="edit-exp-unit" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-hidden">
                        <option value="Umum">Umum</option>
                        <option value="SD">SD</option>
                        <option value="SMP">SMP</option>
                        <option value="SMA">SMA</option>
                        <option value="TK">TK / PGTK</option>
                        <option value="Supporting">Supporting</option>
                    </select>
                </div>
            </div>

            <div>
                <label class="block font-bold text-slate-700 mb-1">Mata Anggaran FKP (COA)</label>
                <select id="edit-exp-coa" class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-hidden">
                    <optgroup label="51411 — PEMELIHARAAN & PERBAIKAN">
                        <option value="51411-001">51411-001 | Pemeliharaan Gedung</option>
                        <option value="51411-002">51411-002 | Pemeliharaan Kolam Renang - Obat Kolam</option>
                        <option value="51411-003">51411-003 | Pemeliharaan Kolam Renang - Treatment Vacum</option>
                        <option value="51411-004">51411-004 | Pemeliharaan Prasarana (Jalan, Pagar, Saluran)</option>
                        <option value="51411-005">51411-005 | Pemeliharaan Kendaraan - Service Motor</option>
                        <option value="51411-006">51411-006 | Pemeliharaan Kendaraan - Service Mobil</option>
                        <option value="51411-007">51411-007 | Pemeliharaan Kendaraan - Pajak Motor</option>
                        <option value="51411-008">51411-008 | Pemeliharaan Kendaraan - Pajak Mobil</option>
                        <option value="51411-009">51411-009 | Pemeliharaan Barang Inventaris</option>
                        <option value="51411-010">51411-010 | Pemeliharaan Lainnya - Fogging</option>
                        <option value="51411-011">51411-011 | Pemeliharaan AC - Cuci</option>
                        <option value="51411-012">51411-012 | Pemeliharaan AC - Service & Perbaikan</option>
                    </optgroup>
                    <optgroup label="51412 — ADMINISTRASI DAN UMUM">
                        <option value="51412-001">51412-001 | Biaya Perizinan</option>
                        <option value="51412-002">51412-002 | Iuran Lingkungan (Keamanan & Kebersihan Kawasan)</option>
                        <option value="51412-004">51412-004 | Admin Bank</option>
                        <option value="51412-005">51412-005 | Sewa Lahan / Ruang Ecopark & ISBI</option>
                        <option value="51412-006">51412-006 | Patty Cash GA (Kas Kecil Operasional)</option>
                        <option value="51412-007">51412-007 | Konsumsi Rapat, Tamu, Olahraga & Lembur</option>
                        <option value="51412-008">51412-008 | Pelatihan SDM Umum & Sertifikasi K3</option>
                    </optgroup>
                    <optgroup label="51413 — ENERGI & KOMUNIKASI">
                        <option value="51413-001">51413-001 | Listrik PLN (YPPI & An Nahl)</option>
                        <option value="51413-002">51413-002 | Telepon & Internet Sekolah</option>
                        <option value="51413-003">51413-003 | Air PDAM & Air Minum Galon</option>
                    </optgroup>
                    <optgroup label="51414 — PERLENGKAPAN">
                        <option value="51414-001">51414-001 | Perlengkapan Kebersihan & Sanitasi OB</option>
                        <option value="51414-002">51414-002 | Perlengkapan Taman & Pertamanan</option>
                        <option value="51414-003">51414-003 | Barang Habis Pakai Chemical & Sabun</option>
                        <option value="51414-004">51414-004 | Barang Habis Pakai Sarpras & Alat Kerja</option>
                        <option value="51414-005">51414-005 | Perlengkapan Umum Sekolah & Logistik</option>
                    </optgroup>
                    <optgroup label="51415 — INVESTASI">
                        <option value="51415-001">51415-001 | Investasi PGTK</option>
                        <option value="51415-002">51415-002 | Investasi SD</option>
                        <option value="51415-003">51415-003 | Investasi SMP</option>
                        <option value="51415-004">51415-004 | Investasi SMA</option>
                        <option value="51415-005">51415-005 | Investasi Supporting & Sarpras Umum</option>
                    </optgroup>
                </select>
            </div>

            <div>
                <label class="block font-bold text-slate-700 mb-1">Uraian Kebutuhan / Rincian Belanja</label>
                <textarea id="edit-exp-desc" rows="3" required class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-hidden"></textarea>
            </div>

            <div class="border-t border-slate-100 pt-3 flex justify-between items-center gap-2">
                <button type="button" onclick="deleteCurrentExpense()" class="px-3 py-2 text-red-600 hover:text-red-700 hover:bg-red-50 font-semibold rounded-xl transition cursor-pointer">
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

    async function loadKeuanganGA() {
        try {
            // 1. Fetch Stats
            const resStats = await fetch('/api/ga/expenses/stats');
            if (resStats.ok) {
                const sData = await resStats.json();
                if (sData.success) {
                    renderFinanceStats(sData);
                }
            }

            // 2. Fetch Expenses Data
            const resExp = await fetch('/api/ga/expenses');
            if (resExp.ok) {
                const eData = await resExp.json();
                if (eData.success) {
                    G_FINANCE_DATA = eData.data || [];
                    filterFinanceData();
                }
            }
        } catch (err) {
            console.error('Error loadKeuanganGA:', err);
        }
    }

    function renderFinanceStats(stats) {
        const grandTotal = stats.grand_total_realisasi || 0;
        const totalTrx = stats.total_transaksi || 0;
        const totalBudget = 1507851796;
        const pct = (grandTotal / totalBudget * 100).toFixed(1);

        document.getElementById('stat-grand-total').innerText = 'Rp ' + grandTotal.toLocaleString('id-ID');
        document.getElementById('stat-total-trx').innerText = totalTrx + ' Transaksi';
        document.getElementById('stat-pct-serapan').innerText = 'Serapan ' + pct + '% dari Plafon FKP';

        // Render 5 Kategori
        const catContainer = document.getElementById('finance-categories-container');
        if (!catContainer) return;

        const fixedCategories = [
            { code: '51411', name: 'Pemeliharaan & Perbaikan', cat: 'PEMELIHARAAN & PERBAIKAN', budget: 181724000 },
            { code: '51412', name: 'Administrasi & Umum / Kas', cat: 'ADMINISTRASI DAN UMUM', budget: 102350000 },
            { code: '51413', name: 'Energi & Komunikasi', cat: 'ENERGI & KOMUNIKASI', budget: 479250000 },
            { code: '51414', name: 'Perlengkapan & Sanitasi', cat: 'PERLENGKAPAN', budget: 86527796 },
            { code: '51415', name: 'Investasi Sarpras', cat: 'INVESTASI', budget: 658000000 }
        ];

        const catMap = {};
        (stats.categories || []).forEach(c => {
            catMap[c.category] = c;
        });

        let html = '';
        fixedCategories.forEach(fc => {
            const row = catMap[fc.cat] || { realisasi: 0, sisa: fc.budget, persentase: 0 };
            const real = row.realisasi || 0;
            const bgt = fc.budget;
            const pctVal = (real / bgt * 100).toFixed(1);
            let barColor = 'bg-emerald-500';
            if (pctVal >= 100) barColor = 'bg-red-500';
            else if (pctVal >= 80) barColor = 'bg-amber-500';

            html += `
            <div class="border border-slate-200/80 rounded-xl p-3 bg-slate-50/50 hover:bg-slate-50 transition">
                <div class="text-[11px] font-bold text-slate-700 truncate" title="${fc.name}">${fc.code} ${fc.name}</div>
                <div class="text-sm font-bold text-slate-800 mt-1">Rp ${real.toLocaleString('id-ID')}</div>
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

    function filterFinanceData() {
        const monthFilter = document.getElementById('filter-finance-month').value.trim();
        const catFilter = document.getElementById('filter-finance-category').value.trim();
        const search = document.getElementById('filter-finance-search').value.toLowerCase().trim();

        const filtered = G_FINANCE_DATA.filter(item => {
            if (monthFilter && item.month_period !== monthFilter) return false;
            if (catFilter && item.main_category !== catFilter) return false;
            if (search) {
                const combined = [
                    item.description, item.vendor_name, item.coa_name,
                    item.kb_code, item.reference_no, item.id
                ].join(' ').toLowerCase();
                if (!combined.includes(search)) return false;
            }
            return true;
        });

        renderFinanceTable(filtered);
    }

    function renderFinanceTable(data) {
        const tbody = document.getElementById('finance-table-tbody');
        const emptyState = document.getElementById('finance-empty-state');
        if (!tbody) return;

        if (data.length === 0) {
            tbody.innerHTML = '';
            emptyState.classList.remove('hidden');
            return;
        }

        emptyState.classList.add('hidden');
        let html = '';

        data.forEach(item => {
            const nominal = item.amount || 0;
            const driveUrl = item.drive_file_url || '';
            const driveBtn = driveUrl ? `
                <a href="${driveUrl}" target="_blank" class="inline-flex items-center gap-1 px-2.5 py-1 bg-blue-50 text-blue-700 hover:bg-blue-100 rounded-lg text-[11px] font-semibold transition" title="Buka Bukti di Google Drive">
                    <i class="fa-brands fa-google-drive text-amber-500"></i>
                    <span>Bukti</span>
                </a>
            ` : `<span class="text-slate-300 text-[11px]">-</span>`;

            html += `
            <tr class="hover:bg-slate-50/80 transition">
                <td class="py-3 px-4">
                    <div class="font-bold text-slate-800">${item.transaction_date || '-'}</div>
                    <div class="text-[10px] text-slate-400 font-mono">${item.kb_code || item.id}</div>
                </td>
                <td class="py-3 px-4">
                    <div class="font-semibold text-slate-700">${item.coa_name || '-'}</div>
                    <div class="text-[10px] text-emerald-600 font-mono">${item.coa_code || '-'}</div>
                </td>
                <td class="py-3 px-4">
                    <div class="font-semibold text-slate-800">${item.vendor_name || '-'}</div>
                    <div class="text-[10px] text-slate-400">${item.bank_info || item.reference_no || ''}</div>
                </td>
                <td class="py-3 px-4 max-w-xs">
                    <p class="text-slate-700 truncate" title="${item.description}">${item.description || '-'}</p>
                </td>
                <td class="py-3 px-4 text-right font-bold text-slate-800">
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
                <a href="${item.drive_file_url}" target="_blank" class="px-3 py-1.5 bg-blue-600 text-white rounded-lg font-semibold text-xs hover:bg-blue-700 transition">Buka File</a>
            </div>
        ` : '';

        const html = `
            <div class="grid grid-cols-2 gap-3 bg-slate-50 p-3 rounded-xl border border-slate-200">
                <div>
                    <span class="text-slate-400 block text-[10px]">Tanggal Transaksi:</span>
                    <span class="font-bold text-slate-800">${item.transaction_date || '-'}</span>
                </div>
                <div>
                    <span class="text-slate-400 block text-[10px]">Nominal Pengeluaran:</span>
                    <span class="font-bold text-emerald-600 text-sm">Rp ${(item.amount || 0).toLocaleString('id-ID')}</span>
                </div>
                <div>
                    <span class="text-slate-400 block text-[10px]">Kode KB (FKP GA):</span>
                    <span class="font-mono font-bold text-slate-700">${item.kb_code || '-'}</span>
                </div>
                <div>
                    <span class="text-slate-400 block text-[10px]">No. Referensi / Nota:</span>
                    <span class="font-mono text-slate-700">${item.reference_no || '-'}</span>
                </div>
                <div>
                    <span class="text-slate-400 block text-[10px]">Penerima / Toko:</span>
                    <span class="font-semibold text-slate-800">${item.vendor_name || '-'}</span>
                </div>
                <div>
                    <span class="text-slate-400 block text-[10px]">Bank / Rekening:</span>
                    <span class="text-slate-700">${item.bank_info || '-'}</span>
                </div>
            </div>

            <div class="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <span class="text-slate-400 block text-[10px]">Mata Anggaran FKP:</span>
                <span class="font-bold text-slate-800">${item.coa_code} — ${item.coa_name}</span>
                <span class="text-slate-500 block text-[11px] mt-0.5">Kategori Induk: ${item.main_category}</span>
                <span class="text-slate-500 block text-[11px]">Sumber: ${item.fund_source} | Unit Target: ${item.unit_target}</span>
            </div>

            <div class="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <span class="text-slate-400 block text-[10px]">Uraian Kebutuhan:</span>
                <p class="text-slate-800 mt-0.5 font-medium">${item.description || '-'}</p>
                ${itemsHtml}
            </div>

            ${driveLinkHtml}

            <div class="text-[11px] text-slate-400 flex justify-between px-1">
                <span>Pelapor: ${item.reporter_name} (+${item.reporter_wa || ''})</span>
                <span>Dicatat: ${item.created_at || '-'}</span>
            </div>
        `;

        document.getElementById('detail-exp-body').innerHTML = html;
        toggleModal('modal-finance-detail');
    }

    function openEditExpenseModal(expId) {
        const item = G_FINANCE_DATA.find(x => x.id === expId);
        if (!item) return;

        document.getElementById('edit-exp-id').value = item.id;
        document.getElementById('edit-exp-date').value = item.transaction_date || '';
        document.getElementById('edit-exp-amount').value = item.amount || 0;
        document.getElementById('edit-exp-vendor').value = item.vendor_name || '';
        document.getElementById('edit-exp-bank').value = item.bank_info || '';
        document.getElementById('edit-exp-ref').value = item.reference_no || '';
        document.getElementById('edit-exp-coa').value = item.coa_code || '51412-006';
        document.getElementById('edit-exp-fund').value = item.fund_source || '2. SPP';
        document.getElementById('edit-exp-unit').value = item.unit_target || 'Umum';
        document.getElementById('edit-exp-desc').value = item.description || '';

        toggleModal('modal-finance-edit');
    }

    async function submitEditExpense(e) {
        e.preventDefault();
        const expId = document.getElementById('edit-exp-id').value;
        const btnSave = document.getElementById('btn-save-edit-expense');

        const payload = {
            transaction_date: document.getElementById('edit-exp-date').value,
            amount: parseInt(document.getElementById('edit-exp-amount').value) || 0,
            vendor_name: document.getElementById('edit-exp-vendor').value.trim(),
            bank_info: document.getElementById('edit-exp-bank').value.trim(),
            reference_no: document.getElementById('edit-exp-ref').value.trim(),
            coa_code: document.getElementById('edit-exp-coa').value,
            fund_source: document.getElementById('edit-exp-fund').value,
            unit_target: document.getElementById('edit-exp-unit').value,
            description: document.getElementById('edit-exp-desc').value.trim()
        };

        btnSave.disabled = true;
        btnSave.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Menyimpan...';

        try {
            const res = await fetch(`/api/ga/expenses/${expId}/update`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();

            if (data.success) {
                toggleModal('modal-finance-edit');
                await loadKeuanganGA();
            } else {
                alert('Gagal memperbarui transaksi: ' + (data.error || 'Terjadi kesalahan'));
            }
        } catch (err) {
            alert('Error: ' + err.message);
        } finally {
            btnSave.disabled = false;
            btnSave.innerHTML = '<i class="fa-solid fa-check"></i> Simpan Perubahan';
        }
    }

    async function deleteCurrentExpense() {
        const expId = document.getElementById('edit-exp-id').value;
        if (!expId) return;

        if (!confirm('Apakah Anda yakin ingin menghapus transaksi ' + expId + '? Data yang dihapus tidak dapat dipulihkan.')) {
            return;
        }

        try {
            const res = await fetch(`/api/ga/expenses/${expId}/delete`, {
                method: 'POST'
            });
            const data = await res.json();

            if (data.success) {
                toggleModal('modal-finance-edit');
                await loadKeuanganGA();
            } else {
                alert('Gagal menghapus: ' + (data.error || 'Terjadi kesalahan'));
            }
        } catch (err) {
            alert('Error: ' + err.message);
        }
    }
</script>
"""
