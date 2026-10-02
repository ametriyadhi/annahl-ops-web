"""
Templates & Komponen Tampilan HTML/JS untuk Modul Pemeliharaan Sarpras (PM)
Berdasarkan Dokumen Standar ISO FM-UMUM-AIS-03-02 Rev.00
"""

TAB_PEMELIHARAAN_HTML = """
<!-- TAB PEMELIHARAAN: PREVENTIVE & CORRECTIVE MAINTENANCE ISO FM-UMUM-AIS-03-02 -->
<div id="tab-pemeliharaan" class="tab-content hidden space-y-6">

    <!-- Header & Action Bar -->
    <div class="bg-white rounded-2xl shadow-xs border border-slate-200/80 p-4 sm:p-6 space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
            <div>
                <div class="flex items-center gap-2">
                    <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-teal-100 text-teal-800 tracking-wider uppercase">Standar ISO FM-UMUM-AIS-03-02</span>
                    <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-100 text-slate-600">Tahun 2025–2026</span>
                </div>
                <h2 class="text-base sm:text-xl font-bold text-slate-800 flex items-center gap-2 mt-1">
                    <i class="fa-solid fa-screwdriver-wrench text-teal-600"></i>
                    Jadwal Pemeliharaan Sarpras & Fasilitas (Indoor & Outdoor)
                </h2>
                <p class="text-xs text-slate-500 mt-0.5">Sistem monitoring preventif berkala: Gedung, AC, Listrik, Kolam Renang, Toilet, Taman, Kandang, Kolam Ikan, dan Fasilitas Kawasan.</p>
            </div>
            <div class="flex items-center gap-2 sm:gap-3 flex-wrap">
                <button type="button" onclick="loadPmData()" class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition flex items-center gap-1.5 cursor-pointer">
                    <i class="fa-solid fa-arrows-rotate"></i> Refresh
                </button>
                <a href="/export/pm" target="_blank" class="px-3 py-1.5 bg-slate-700 hover:bg-slate-800 text-white text-xs font-semibold rounded-lg transition shadow-xs flex items-center gap-1.5">
                    <i class="fa-solid fa-file-csv"></i> Ekspor Rekap ISO
                </a>
                <button type="button" onclick="openModalPmExecute()" class="px-3.5 py-1.5 bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold rounded-lg transition shadow-xs flex items-center gap-1.5 cursor-pointer">
                    <i class="fa-solid fa-plus-circle"></i> Catat Pelaksanaan PM
                </button>
            </div>
        </div>

        <!-- 4 Top KPI Metric Cards -->
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
            <div class="bg-gradient-to-br from-slate-50 to-slate-100/60 border border-slate-200/80 rounded-xl p-3 sm:p-4">
                <span class="text-[10px] sm:text-xs font-bold text-slate-500 uppercase tracking-wider block">Agenda PM Bulan Ini</span>
                <div class="mt-1 flex items-baseline gap-2">
                    <span id="pm-stat-total" class="text-xl sm:text-2xl font-black text-slate-800">0</span>
                    <span class="text-[10px] text-slate-400 font-semibold">butir kerja</span>
                </div>
                <span class="text-[10px] text-slate-500 mt-1 block">Indoor & Outdoor Aktif</span>
            </div>

            <div class="bg-gradient-to-br from-teal-50 to-emerald-50/60 border border-teal-200/80 rounded-xl p-3 sm:p-4">
                <span class="text-[10px] sm:text-xs font-bold text-teal-800 uppercase tracking-wider block">Kepatuhan Realisasi</span>
                <div class="mt-1 flex items-baseline gap-2">
                    <span id="pm-stat-compliance" class="text-xl sm:text-2xl font-black text-teal-700">0%</span>
                    <span id="pm-stat-completed" class="text-[10px] text-teal-600 font-semibold">0 selesai</span>
                </div>
                <div class="w-full bg-teal-200/50 rounded-full h-1.5 mt-2 overflow-hidden">
                    <div id="pm-stat-progress-bar" class="bg-teal-600 h-1.5 rounded-full transition-all duration-500" style="width: 0%"></div>
                </div>
            </div>

            <div class="bg-gradient-to-br from-amber-50 to-orange-50/60 border border-amber-200/80 rounded-xl p-3 sm:p-4">
                <span class="text-[10px] sm:text-xs font-bold text-amber-800 uppercase tracking-wider block">Beban Unit Pelaksana</span>
                <div class="mt-1 flex items-center gap-2 text-xs font-bold text-slate-700">
                    <span class="inline-flex items-center gap-1 text-emerald-700 bg-emerald-100/60 px-1.5 py-0.5 rounded">🌿 <span id="pm-stat-gardener">0</span></span>
                    <span class="inline-flex items-center gap-1 text-sky-700 bg-sky-100/60 px-1.5 py-0.5 rounded">🧹 <span id="pm-stat-ob">0</span></span>
                    <span class="inline-flex items-center gap-1 text-slate-700 bg-slate-200/60 px-1.5 py-0.5 rounded">🛠️ <span id="pm-stat-vendor">0</span></span>
                </div>
                <span class="text-[10px] text-amber-700 mt-1 block">Gardener | OB | Vendor</span>
            </div>

            <div class="bg-gradient-to-br from-rose-50 to-red-50/60 border border-rose-200/80 rounded-xl p-3 sm:p-4">
                <span class="text-[10px] sm:text-xs font-bold text-rose-800 uppercase tracking-wider block">Status & Perhatian</span>
                <div class="mt-1 flex items-baseline gap-2">
                    <span id="pm-stat-pending" class="text-xl sm:text-2xl font-black text-rose-700">0</span>
                    <span class="text-[10px] text-rose-600 font-semibold">pending / jatuh tempo</span>
                </div>
                <span id="pm-stat-overdue" class="text-[10px] text-rose-600 mt-1 block">0 terlambat (overdue)</span>
            </div>
        </div>

        <!-- Filter & View Switcher Bar -->
        <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-3 border-t border-slate-100 pt-3">
            <div class="flex items-center gap-2 flex-wrap">
                <!-- Filter Lingkup -->
                <div class="flex items-center bg-slate-100 p-0.5 rounded-lg border border-slate-200/60 text-xs">
                    <button type="button" onclick="setPmScopeFilter('ALL')" id="pm-btn-scope-all" class="px-2.5 py-1 rounded-md font-semibold text-slate-700 bg-white shadow-xs transition">Semua</button>
                    <button type="button" onclick="setPmScopeFilter('INDOOR')" id="pm-btn-scope-indoor" class="px-2.5 py-1 rounded-md font-semibold text-slate-500 hover:text-slate-700 transition">Indoor & Gedung</button>
                    <button type="button" onclick="setPmScopeFilter('OUTDOOR')" id="pm-btn-scope-outdoor" class="px-2.5 py-1 rounded-md font-semibold text-slate-500 hover:text-slate-700 transition">Outdoor & Taman</button>
                </div>

                <!-- Filter Pelaksana -->
                <select id="pm-filter-executor" onchange="filterPmItems()" class="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 font-semibold text-slate-700 focus:outline-none focus:ring-1 focus:ring-teal-500">
                    <option value="ALL">Semua Pelaksana</option>
                    <option value="GARDENER">🌿 Unit Gardener (Taman/Ecopark)</option>
                    <option value="OB">🧹 Unit Office Boy (Toilet/Ruang/AC)</option>
                    <option value="VENDOR">🛠️ Vendor / Sarpras Spesialis</option>
                </select>

                <!-- Filter Frekuensi -->
                <select id="pm-filter-frequency" onchange="filterPmItems()" class="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 font-semibold text-slate-700 focus:outline-none focus:ring-1 focus:ring-teal-500">
                    <option value="ALL">Semua Frekuensi</option>
                    <option value="RUTIN">Rutin (Harian / 2x Sehari / 3x Sepekan)</option>
                    <option value="2 Pekan Sekali">2 Pekan Sekali</option>
                    <option value="BERKALA">Berkala (Bulanan / Semester / Tahunan)</option>
                    <option value="Kondisional">Kondisional (Setiap Rusak)</option>
                </select>
            </div>

            <!-- View Switcher Toggle -->
            <div class="flex items-center gap-1.5 bg-slate-100 p-1 rounded-lg border border-slate-200/80 text-xs">
                <button type="button" onclick="switchPmView('matrix')" id="btn-pm-view-matrix" class="px-3 py-1 font-semibold rounded-md bg-white text-teal-800 shadow-xs flex items-center gap-1.5 transition">
                    <i class="fa-solid fa-table-cells"></i> Matriks Kalender 12 Bulan (ISO)
                </button>
                <button type="button" onclick="switchPmView('cards')" id="btn-pm-view-cards" class="px-3 py-1 font-semibold rounded-md text-slate-600 hover:text-slate-800 flex items-center gap-1.5 transition">
                    <i class="fa-solid fa-list-check"></i> Kartu Agenda Bulan Ini
                </button>
            </div>
        </div>
    </div>

    <!-- VIEW 1: MATRIKS KALENDER 12 BULAN (STANDAR FM-UMUM-AIS-03-02) -->
    <div id="pm-view-matrix" class="bg-white rounded-2xl shadow-xs border border-slate-200/80 overflow-hidden">
        <div class="p-4 bg-slate-50/80 border-b border-slate-200/80 flex items-center justify-between flex-wrap gap-2">
            <div>
                <h3 class="text-sm font-bold text-slate-800 flex items-center gap-2">
                    <i class="fa-solid fa-calendar-days text-teal-600"></i>
                    Matriks Jadwal Pemeliharaan Sarana & Prasarana Tahun Ajaran 2025–2026
                </h3>
                <p class="text-xs text-slate-500">Kolom Bulan 1–12 merefleksikan jadwal resmi form ISO. Kolom dengan aksen teal adalah bulan berjalan aktif.</p>
            </div>
            <div class="flex items-center gap-2 text-xs">
                <span class="inline-flex items-center gap-1 text-[11px] text-slate-600"><span class="w-3 h-3 bg-teal-500 rounded-sm inline-block"></span> Terjadwal</span>
                <span class="inline-flex items-center gap-1 text-[11px] text-slate-600"><span class="w-3 h-3 bg-emerald-500 rounded-sm inline-block"></span> Terealisasi</span>
            </div>
        </div>

        <div class="overflow-x-auto">
            <table class="w-full text-left text-xs border-collapse">
                <thead>
                    <tr class="bg-slate-100/90 text-slate-700 font-bold border-b border-slate-200 uppercase tracking-wider text-[10px]">
                        <th class="py-3 px-3 w-10 text-center">No</th>
                        <th class="py-3 px-3 min-w-[140px]">Sarpras / Objek</th>
                        <th class="py-3 px-3 min-w-[180px]">Butir & Indikator Mutu</th>
                        <th class="py-3 px-2 w-24 text-center">Frekuensi</th>
                        <th class="py-3 px-2 w-28 text-center">Pelaksana</th>
                        <th class="py-3 px-2 w-28 text-center">Penanggung Jawab</th>
                        <!-- Bulan 1 s.d. 12 -->
                        <th class="py-3 px-1 w-7 text-center">1</th>
                        <th class="py-3 px-1 w-7 text-center">2</th>
                        <th class="py-3 px-1 w-7 text-center">3</th>
                        <th class="py-3 px-1 w-7 text-center">4</th>
                        <th class="py-3 px-1 w-7 text-center">5</th>
                        <th class="py-3 px-1 w-7 text-center">6</th>
                        <th class="py-3 px-1 w-7 text-center">7</th>
                        <th class="py-3 px-1 w-7 text-center">8</th>
                        <th class="py-3 px-1 w-7 text-center">9</th>
                        <th class="py-3 px-1 w-7 text-center bg-teal-100 text-teal-900 border-x border-teal-200">10</th>
                        <th class="py-3 px-1 w-7 text-center">11</th>
                        <th class="py-3 px-1 w-7 text-center">12</th>
                        <th class="py-3 px-3 w-20 text-center">Aksi</th>
                    </tr>
                </thead>
                <tbody id="pm-matrix-tbody" class="divide-y divide-slate-100 text-slate-700">
                    <tr><td colspan="19" class="text-center py-8 text-slate-400">Memuat matriks data pemeliharaan ISO...</td></tr>
                </tbody>
            </table>
        </div>
    </div>

    <!-- VIEW 2: KARTU AGENDA AKTIF BULAN BERJALAN -->
    <div id="pm-view-cards" class="hidden space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" id="pm-cards-container">
            <!-- Dynamic Schedule Cards will be injected here -->
        </div>
    </div>

    <!-- SEKSI 3: RIWAYAT PELAKSANAAN & BUKTI FISIK TERKINI -->
    <div class="bg-white rounded-2xl shadow-xs border border-slate-200/80 p-4 sm:p-6 space-y-4">
        <div class="flex items-center justify-between border-b border-slate-100 pb-3 flex-wrap gap-2">
            <div>
                <h3 class="text-sm sm:text-base font-bold text-slate-800 flex items-center gap-2">
                    <i class="fa-solid fa-clock-rotate-left text-slate-600"></i>
                    Riwayat Pelaksanaan & Bukti Fisik Pemeliharaan Terakhir
                </h3>
                <p class="text-xs text-slate-500">Dokumentasi hasil pemeriksaan, rating kondisi sarpras, dan foto verifikasi lapangan.</p>
            </div>
            <span class="text-xs font-semibold text-slate-500">Menampilkan 10 log terakhir</span>
        </div>

        <div class="overflow-x-auto">
            <table class="w-full text-left text-xs border-collapse">
                <thead>
                    <tr class="bg-slate-50 text-slate-600 font-bold border-b border-slate-200 uppercase tracking-wider text-[10px]">
                        <th class="py-2.5 px-3">Tanggal & Waktu</th>
                        <th class="py-2.5 px-3">Sarpras / Butir Pekerjaan</th>
                        <th class="py-2.5 px-3">Pelaksana</th>
                        <th class="py-2.5 px-3 text-center">Kondisi Hasil</th>
                        <th class="py-2.5 px-3 text-center">Foto Bukti</th>
                        <th class="py-2.5 px-3">Temuan & Tindakan</th>
                        <th class="py-2.5 px-3 text-center">Tiket Sarpras</th>
                    </tr>
                </thead>
                <tbody id="pm-logs-tbody" class="divide-y divide-slate-100">
                    <tr><td colspan="7" class="text-center py-6 text-slate-400">Belum ada riwayat pelaksanaan pemeliharaan terbaru.</td></tr>
                </tbody>
            </table>
        </div>
    </div>
</div>

<!-- MODAL FORM: CATAT PELAKSANAAN PEMELIHARAAN (PM) -->
<div id="modal-pm-execute" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs hidden">
    <div class="bg-white rounded-2xl shadow-xl border border-slate-200 w-full max-w-xl max-h-[90vh] overflow-y-auto">
        <div class="p-5 border-b border-slate-100 flex items-center justify-between">
            <div class="flex items-center gap-2">
                <div class="w-8 h-8 rounded-lg bg-teal-100 text-teal-700 flex items-center justify-center font-bold text-sm">
                    <i class="fa-solid fa-wrench"></i>
                </div>
                <div>
                    <h3 class="font-bold text-slate-800 text-sm sm:text-base">Catat Pelaksanaan Pemeliharaan Sarpras</h3>
                    <p class="text-xs text-slate-500">Unggah bukti foto before/after dan catatan hasil pemeriksaan</p>
                </div>
            </div>
            <button type="button" onclick="closeModalPmExecute()" class="text-slate-400 hover:text-slate-600 text-lg cursor-pointer">
                <i class="fa-solid fa-xmark"></i>
            </button>
        </div>

        <form id="form-pm-execute" onsubmit="submitPmExecution(event)" class="p-5 space-y-4 text-xs">
            <input type="hidden" id="pm-form-schedule-id" name="schedule_id" value="">
            
            <!-- Pilih Sarpras Master -->
            <div>
                <label class="block font-semibold text-slate-700 mb-1">Butir Pemeliharaan Sarpras (Standar ISO) <span class="text-rose-500">*</span></label>
                <select id="pm-form-master-id" name="master_id" required class="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 font-medium text-slate-800 focus:outline-none focus:ring-1 focus:ring-teal-500">
                    <option value="">-- Pilih Butir Pekerjaan Pemeliharaan --</option>
                </select>
                <div id="pm-form-indicator-hint" class="mt-1 text-[11px] text-teal-700 font-medium hidden">
                    <i class="fa-solid fa-circle-check"></i> Standar Mutu: <span id="pm-form-indicator-text"></span>
                </div>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <!-- Tanggal Pelaksanaan -->
                <div>
                    <label class="block font-semibold text-slate-700 mb-1">Tanggal Pelaksanaan <span class="text-rose-500">*</span></label>
                    <input type="date" id="pm-form-date" name="execution_date" required class="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 font-medium text-slate-800 focus:outline-none focus:ring-1 focus:ring-teal-500">
                </div>

                <!-- Pelaksana -->
                <div>
                    <label class="block font-semibold text-slate-700 mb-1">Unit Pelaksana <span class="text-rose-500">*</span></label>
                    <select id="pm-form-executor-type" name="executor_type" required class="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 font-medium text-slate-800 focus:outline-none focus:ring-1 focus:ring-teal-500">
                        <option value="GARDENER">🌿 Unit Gardener (Taman & Ternak)</option>
                        <option value="OB">🧹 Unit Office Boy (Toilet & Gedung)</option>
                        <option value="VENDOR">🛠️ Vendor Rekanan / Teknisi Sarpras</option>
                    </select>
                </div>
            </div>

            <!-- Nama Petugas / Teknisi -->
            <div>
                <label class="block font-semibold text-slate-700 mb-1">Nama Petugas / Vendor Pelaksana <span class="text-rose-500">*</span></label>
                <input type="text" id="pm-form-executor-name" name="executor_name" placeholder="Contoh: Pak Samad (Gardener) / Pak Masdik (Sarpras)" required class="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 font-medium text-slate-800 focus:outline-none focus:ring-1 focus:ring-teal-500">
            </div>

            <!-- Kondisi Hasil Pemeriksaan -->
            <div>
                <label class="block font-semibold text-slate-700 mb-1.5">Kondisi Hasil Pemeriksaan <span class="text-rose-500">*</span></label>
                <div class="grid grid-cols-3 gap-2">
                    <label class="flex flex-col items-center p-2.5 bg-emerald-50/60 border border-emerald-200 rounded-xl cursor-pointer hover:bg-emerald-100/60 transition">
                        <input type="radio" name="condition_rating" value="BAIK" checked class="text-emerald-600 focus:ring-emerald-500">
                        <span class="font-bold text-emerald-800 mt-1">🟢 BAIK / PRIMA</span>
                        <span class="text-[10px] text-emerald-600 text-center">Sesuai standar mutu</span>
                    </label>
                    <label class="flex flex-col items-center p-2.5 bg-amber-50/60 border border-amber-200 rounded-xl cursor-pointer hover:bg-amber-100/60 transition">
                        <input type="radio" name="condition_rating" value="CUKUP" class="text-amber-600 focus:ring-amber-500">
                        <span class="font-bold text-amber-800 mt-1">🟡 CUKUP</span>
                        <span class="text-[10px] text-amber-600 text-center">Perlu perhatian</span>
                    </label>
                    <label class="flex flex-col items-center p-2.5 bg-rose-50/60 border border-rose-200 rounded-xl cursor-pointer hover:bg-rose-100/60 transition">
                        <input type="radio" name="condition_rating" value="RUSAK_BUTUH_PERBAIKAN" class="text-rose-600 focus:ring-rose-500">
                        <span class="font-bold text-rose-800 mt-1">🔴 RUSAK</span>
                        <span class="text-[10px] text-rose-600 text-center">Butuh perbaikan sarpras</span>
                    </label>
                </div>
            </div>

            <!-- Catatan Temuan & Tindakan -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                    <label class="block font-semibold text-slate-700 mb-1">Catatan Temuan Lapangan</label>
                    <textarea id="pm-form-findings" name="finding_notes" rows="2" placeholder="Catatan kondisi spesifik fasilitas saat diperiksa..." class="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 font-medium text-slate-800 focus:outline-none focus:ring-1 focus:ring-teal-500"></textarea>
                </div>
                <div>
                    <label class="block font-semibold text-slate-700 mb-1">Tindakan yang Telah Dilakukan</label>
                    <textarea id="pm-form-action" name="action_taken" rows="2" placeholder="Misal: Sudah dipotong rapi, dicuci bersih, dikuras..." class="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 font-medium text-slate-800 focus:outline-none focus:ring-1 focus:ring-teal-500"></textarea>
                </div>
            </div>

            <!-- Foto Bukti Sebelum & Sesudah -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                    <label class="block font-semibold text-slate-700 mb-1">URL / Link Foto Sebelum (Before)</label>
                    <input type="url" id="pm-form-photo-before" name="photo_before_url" placeholder="https://..." class="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 font-medium text-slate-800 focus:outline-none focus:ring-1 focus:ring-teal-500">
                </div>
                <div>
                    <label class="block font-semibold text-slate-700 mb-1">URL / Link Foto Sesudah (After)</label>
                    <input type="url" id="pm-form-photo-after" name="photo_after_url" placeholder="https://..." class="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 font-medium text-slate-800 focus:outline-none focus:ring-1 focus:ring-teal-500">
                </div>
            </div>

            <!-- Auto-Ticket Checkbox -->
            <div class="bg-slate-50 border border-slate-200 p-3 rounded-xl flex items-start gap-2.5">
                <input type="checkbox" id="pm-form-create-ticket" name="create_ticket" class="mt-0.5 rounded text-teal-600 focus:ring-teal-500">
                <label for="pm-form-create-ticket" class="cursor-pointer text-slate-700 leading-tight">
                    <span class="font-bold text-slate-800">Terbitkan Tiket Perbaikan Sarpras Otomatis</span>
                    <span class="block text-[11px] text-slate-500 mt-0.5">Centang jika fasilitas memerlukan penanganan perbaikan khusus oleh teknisi sarpras/sipil/listrik.</span>
                </label>
            </div>

            <div class="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
                <button type="button" onclick="closeModalPmExecute()" class="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-lg transition cursor-pointer">Batal</button>
                <button type="submit" id="pm-form-btn-submit" class="px-5 py-2 bg-teal-600 hover:bg-teal-700 text-white font-semibold rounded-lg transition shadow-xs cursor-pointer flex items-center gap-1.5">
                    <i class="fa-solid fa-check"></i> Simpan Laporan Pelaksanaan
                </button>
            </div>
        </form>
    </div>
</div>

<!-- MODAL PHOTO PREVIEW -->
<div id="modal-pm-photo-view" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-xs hidden" onclick="closePmPhotoPreview()">
    <div class="max-w-2xl max-h-[85vh] p-2 bg-white rounded-2xl overflow-hidden shadow-2xl" onclick="event.stopPropagation()">
        <div class="flex items-center justify-between p-2 border-b border-slate-100">
            <span id="pm-photo-preview-title" class="text-xs font-bold text-slate-700">Foto Bukti Pelaksanaan</span>
            <button type="button" onclick="closePmPhotoPreview()" class="text-slate-400 hover:text-slate-600 text-lg cursor-pointer">
                <i class="fa-solid fa-xmark"></i>
            </button>
        </div>
        <div class="p-2 flex items-center justify-center">
            <img id="pm-photo-preview-img" src="" alt="Foto Pemeliharaan" class="max-h-[70vh] rounded-lg object-contain">
        </div>
    </div>
</div>
"""

PM_CLIENT_SCRIPT = """
<script>
// --- CLIENT CONTROLLER MODUL PEMELIHARAAN SARPRAS (ISO FM-UMUM-AIS-03-02) ---

let pmDataCache = null;
let currentPmScope = 'ALL';
let currentPmView = 'matrix';

document.addEventListener('DOMContentLoaded', () => {
    // Inisialisasi tanggal form hari ini
    const elDate = document.getElementById('pm-form-date');
    if (elDate) {
        elDate.value = new Date().toISOString().split('T')[0];
    }
});

function switchPmView(viewMode) {
    currentPmView = viewMode;
    const viewMatrix = document.getElementById('pm-view-matrix');
    const viewCards = document.getElementById('pm-view-cards');
    const btnMatrix = document.getElementById('btn-pm-view-matrix');
    const btnCards = document.getElementById('btn-pm-view-cards');

    if (viewMode === 'matrix') {
        viewMatrix.classList.remove('hidden');
        viewCards.classList.add('hidden');
        btnMatrix.className = "px-3 py-1 font-semibold rounded-md bg-white text-teal-800 shadow-xs flex items-center gap-1.5 transition";
        btnCards.className = "px-3 py-1 font-semibold rounded-md text-slate-600 hover:text-slate-800 flex items-center gap-1.5 transition";
    } else {
        viewMatrix.classList.add('hidden');
        viewCards.classList.remove('hidden');
        btnCards.className = "px-3 py-1 font-semibold rounded-md bg-white text-teal-800 shadow-xs flex items-center gap-1.5 transition";
        btnMatrix.className = "px-3 py-1 font-semibold rounded-md text-slate-600 hover:text-slate-800 flex items-center gap-1.5 transition";
    }
}

function setPmScopeFilter(scope) {
    currentPmScope = scope;
    const btnAll = document.getElementById('pm-btn-scope-all');
    const btnIndoor = document.getElementById('pm-btn-scope-indoor');
    const btnOutdoor = document.getElementById('pm-btn-scope-outdoor');

    [btnAll, btnIndoor, btnOutdoor].forEach(b => {
        b.className = "px-2.5 py-1 rounded-md font-semibold text-slate-500 hover:text-slate-700 transition";
    });

    if (scope === 'ALL') {
        btnAll.className = "px-2.5 py-1 rounded-md font-semibold text-slate-700 bg-white shadow-xs transition";
    } else if (scope === 'INDOOR') {
        btnIndoor.className = "px-2.5 py-1 rounded-md font-semibold text-slate-700 bg-white shadow-xs transition";
    } else if (scope === 'OUTDOOR') {
        btnOutdoor.className = "px-2.5 py-1 rounded-md font-semibold text-slate-700 bg-white shadow-xs transition";
    }

    filterPmItems();
}

async function loadPmData() {
    try {
        const res = await fetch('/api/ops/pm/summary');
        const data = await res.json();
        pmDataCache = data;

        // 1. Update Metrik KPI
        document.getElementById('pm-stat-total').innerText = data.total || 0;
        document.getElementById('pm-stat-compliance').innerText = (data.compliance_pct || 0) + '%';
        document.getElementById('pm-stat-completed').innerText = (data.completed || 0) + ' selesai';
        document.getElementById('pm-stat-progress-bar').style.width = (data.compliance_pct || 0) + '%';
        document.getElementById('pm-stat-gardener').innerText = data.by_executor?.gardener || 0;
        document.getElementById('pm-stat-ob').innerText = data.by_executor?.ob || 0;
        document.getElementById('pm-stat-vendor').innerText = data.by_executor?.vendor || 0;
        document.getElementById('pm-stat-pending').innerText = data.pending || 0;
        document.getElementById('pm-stat-overdue').innerText = (data.overdue || 0) + ' terlambat (overdue)';

        // 2. Populate Dropdown Master di Modal
        const selMaster = document.getElementById('pm-form-master-id');
        if (selMaster && data.schedules) {
            selMaster.innerHTML = '<option value="">-- Pilih Butir Pekerjaan Pemeliharaan --</option>';
            data.schedules.forEach(s => {
                const opt = document.createElement('option');
                opt.value = s.master_id;
                opt.dataset.scheduleId = s.id;
                opt.dataset.indicator = s.indicator_standard;
                opt.dataset.executorType = s.executor_type;
                opt.dataset.executorName = s.assigned_to;
                opt.innerText = `[${s.scope}] ${s.category} - ${s.item_name} (${s.frequency})`;
                selMaster.appendChild(opt);
            });
        }

        // 3. Render Views
        filterPmItems();
        renderPmLogs(data.recent_logs || []);

    } catch (err) {
        console.error('Error loadPmData:', err);
    }
}

function filterPmItems() {
    if (!pmDataCache || !pmDataCache.schedules) return;

    const executorFilter = document.getElementById('pm-filter-executor').value;
    const freqFilter = document.getElementById('pm-filter-frequency').value;

    const filtered = pmDataCache.schedules.filter(s => {
        // Filter Scope
        if (currentPmScope !== 'ALL' && s.scope !== currentPmScope) return false;
        // Filter Executor
        if (executorFilter !== 'ALL' && s.executor_type !== executorFilter) return false;
        // Filter Frequency
        if (freqFilter === 'RUTIN') {
            if (!['2x Sehari', 'Setiap Hari', '3x Sepekan'].includes(s.frequency)) return false;
        } else if (freqFilter === 'BERKALA') {
            if (['2x Sehari', 'Setiap Hari', '3x Sepekan', '2 Pekan Sekali', 'Kondisional'].includes(s.frequency)) return false;
        } else if (freqFilter !== 'ALL') {
            if (s.frequency !== freqFilter) return false;
        }
        return true;
    });

    renderPmMatrix(filtered);
    renderPmCards(filtered);
}

function renderPmMatrix(items) {
    const tbody = document.getElementById('pm-matrix-tbody');
    if (!tbody) return;

    if (!items.length) {
        tbody.innerHTML = '<tr><td colspan="19" class="text-center py-8 text-slate-400">Tidak ada butir pemeliharaan yang cocok dengan filter.</td></tr>';
        return;
    }

    const currentMonth = new Date().getMonth() + 1; // 10

    tbody.innerHTML = items.map((item, idx) => {
        const months = JSON.parse(item.schedule_months_json || '[]');
        const isCompleted = item.status === 'COMPLETED';

        let executorBadge = '';
        if (item.executor_type === 'GARDENER') {
            executorBadge = '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 inline-flex items-center gap-1">🌿 Gardener</span>';
        } else if (item.executor_type === 'OB') {
            executorBadge = '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-sky-100 text-sky-800 inline-flex items-center gap-1">🧹 Office Boy</span>';
        } else {
            executorBadge = '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-200 text-slate-700 inline-flex items-center gap-1">🛠️ Vendor/Sarpras</span>';
        }

        // Render Kolom Bulan 1..12
        let monthCols = '';
        for (let m = 1; m <= 12; m++) {
            const isScheduled = months.includes(m) || ['2x Sehari', 'Setiap Hari', '3x Sepekan', '2 Pekan Sekali'].includes(item.frequency);
            const isCurrentMonth = (m === currentMonth);
            const bgClass = isCurrentMonth ? 'bg-teal-50/70 border-x border-teal-100 font-bold' : '';

            let mark = '';
            if (isScheduled) {
                if (isCurrentMonth && isCompleted) {
                    mark = '<span class="text-emerald-600 font-black text-sm">✓</span>';
                } else if (isCurrentMonth) {
                    mark = '<span class="text-teal-600 font-bold">✓</span>';
                } else {
                    mark = '<span class="text-slate-400">✓</span>';
                }
            } else {
                mark = '<span class="text-slate-200">-</span>';
            }

            monthCols += `<td class="py-2.5 px-1 text-center ${bgClass}">${mark}</td>`;
        }

        return `
            <tr class="hover:bg-slate-50/80 transition">
                <td class="py-2.5 px-3 text-center text-slate-400 font-semibold">${idx + 1}</td>
                <td class="py-2.5 px-3">
                    <span class="font-bold text-slate-800 block">${escapeHtml(item.category)}</span>
                    <span class="text-[10px] text-slate-500">${escapeHtml(item.sub_category || item.scope)}</span>
                </td>
                <td class="py-2.5 px-3">
                    <span class="font-semibold text-slate-800 block">${escapeHtml(item.item_name)}</span>
                    <span class="text-[10px] text-teal-700 block"><i class="fa-solid fa-bullseye text-[9px]"></i> ${escapeHtml(item.indicator_standard)}</span>
                </td>
                <td class="py-2.5 px-2 text-center">
                    <span class="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-700 block">${escapeHtml(item.frequency)}</span>
                </td>
                <td class="py-2.5 px-2 text-center">${executorBadge}</td>
                <td class="py-2.5 px-2 text-center text-[11px] font-medium text-slate-600">${escapeHtml(item.pj_role)}</td>
                ${monthCols}
                <td class="py-2.5 px-3 text-center">
                    <button type="button" onclick="openModalPmExecute(${item.master_id}, '${item.id}', '${escapeHtml(item.item_name)}', '${item.executor_type}')" class="px-2.5 py-1 bg-teal-50 hover:bg-teal-600 text-teal-700 hover:text-white rounded text-[10px] font-bold transition shadow-2xs cursor-pointer">
                        ${isCompleted ? '✓ Selesai' : 'Lapor PM'}
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

function renderPmCards(items) {
    const container = document.getElementById('pm-cards-container');
    if (!container) return;

    if (!items.length) {
        container.innerHTML = '<div class="col-span-3 text-center py-12 text-slate-400">Tidak ada butir pemeliharaan aktif.</div>';
        return;
    }

    container.innerHTML = items.map(s => {
        let statusBadge = '<span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800">PENDING</span>';
        if (s.status === 'COMPLETED') {
            statusBadge = '<span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">TEREALISASI</span>';
        } else if (s.status === 'OVERDUE') {
            statusBadge = '<span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800">OVERDUE</span>';
        }

        let scopeIcon = s.scope === 'INDOOR' ? '🏢 Gedung' : '🌿 Outdoor';

        return `
            <div class="bg-white rounded-xl border border-slate-200/80 p-4 shadow-xs hover:shadow-md transition space-y-3 flex flex-col justify-between">
                <div class="space-y-2">
                    <div class="flex items-center justify-between">
                        <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">${scopeIcon} • ${escapeHtml(s.category)}</span>
                        ${statusBadge}
                    </div>
                    <h4 class="font-bold text-slate-800 text-sm">${escapeHtml(s.item_name)}</h4>
                    <p class="text-xs text-slate-600 bg-slate-50 p-2 rounded-lg border border-slate-100">
                        <span class="font-semibold text-teal-800 block text-[10px]">STANDAR MUTU:</span>
                        ${escapeHtml(s.indicator_standard)}
                    </p>
                    <div class="text-[11px] text-slate-500 space-y-1">
                        <div><i class="fa-solid fa-arrows-rotate text-slate-400"></i> Frekuensi: <span class="font-semibold text-slate-700">${escapeHtml(s.frequency)}</span></div>
                        <div><i class="fa-solid fa-user-gear text-slate-400"></i> Pelaksana: <span class="font-semibold text-slate-700">${escapeHtml(s.assigned_to || s.executor_type)}</span></div>
                    </div>
                </div>

                <div class="pt-3 border-t border-slate-100 flex items-center justify-between">
                    <span class="text-[10px] text-slate-400">Jatuh tempo: ${s.due_date || '-'}</span>
                    <button type="button" onclick="openModalPmExecute(${s.master_id}, '${s.id}', '${escapeHtml(s.item_name)}', '${s.executor_type}')" class="px-3 py-1.5 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-xs font-bold transition shadow-xs cursor-pointer">
                        ${s.status === 'COMPLETED' ? 'Lihat / Update' : 'Catat Eksekusi'}
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

function renderPmLogs(logs) {
    const tbody = document.getElementById('pm-logs-tbody');
    if (!tbody) return;

    if (!logs.length) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center py-6 text-slate-400">Belum ada riwayat pelaksanaan pemeliharaan terbaru.</td></tr>';
        return;
    }

    tbody.innerHTML = logs.map(l => {
        let condBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">BAIK</span>';
        if (l.condition_rating === 'CUKUP') {
            condBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800">CUKUP</span>';
        } else if (l.condition_rating === 'RUSAK_BUTUH_PERBAIKAN') {
            condBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-800">RUSAK</span>';
        }

        let photoThumb = '<span class="text-slate-300">-</span>';
        if (l.photo_after_url || l.photo_before_url) {
            const url = l.photo_after_url || l.photo_before_url;
            photoThumb = `
                <img src="${escapeHtml(url)}" onclick="openPmPhotoPreview('${escapeHtml(url)}', '${escapeHtml(l.item_name)}')" class="w-9 h-9 object-cover rounded-lg border border-slate-200 cursor-pointer hover:opacity-80 transition mx-auto">
            `;
        }

        let ticketBadge = '<span class="text-slate-300">-</span>';
        if (l.ticket_id) {
            ticketBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-800">${escapeHtml(l.ticket_id)}</span>`;
        }

        return `
            <tr class="hover:bg-slate-50 transition">
                <td class="py-2.5 px-3">
                    <span class="font-bold text-slate-800 block">${l.execution_date}</span>
                    <span class="text-[10px] text-slate-400">${l.execution_time || ''}</span>
                </td>
                <td class="py-2.5 px-3">
                    <span class="font-bold text-slate-800 block">${escapeHtml(l.item_name)}</span>
                    <span class="text-[10px] text-slate-500">${escapeHtml(l.category)} (${escapeHtml(l.scope)})</span>
                </td>
                <td class="py-2.5 px-3">
                    <span class="font-semibold text-slate-700 block">${escapeHtml(l.executor_name)}</span>
                    <span class="text-[10px] text-slate-400">${escapeHtml(l.executor_type)}</span>
                </td>
                <td class="py-2.5 px-3 text-center">${condBadge}</td>
                <td class="py-2.5 px-3 text-center">${photoThumb}</td>
                <td class="py-2.5 px-3 max-w-xs">
                    <span class="text-slate-800 block font-medium">${escapeHtml(l.finding_notes || 'Pemeriksaan rutin')}</span>
                    ${l.action_taken ? `<span class="text-[10px] text-teal-700 block">Tindakan: ${escapeHtml(l.action_taken)}</span>` : ''}
                </td>
                <td class="py-2.5 px-3 text-center">${ticketBadge}</td>
            </tr>
        `;
    }).join('');
}

function openModalPmExecute(masterId, scheduleId, itemName, executorType) {
    const modal = document.getElementById('modal-pm-execute');
    if (!modal) return;

    const selMaster = document.getElementById('pm-form-master-id');
    const inputSched = document.getElementById('pm-form-schedule-id');
    const selExecutor = document.getElementById('pm-form-executor-type');

    if (masterId && selMaster) {
        selMaster.value = masterId;
    }
    if (scheduleId && inputSched) {
        inputSched.value = scheduleId;
    }
    if (executorType && selExecutor) {
        selExecutor.value = executorType;
    }

    modal.classList.remove('hidden');
}

function closeModalPmExecute() {
    const modal = document.getElementById('modal-pm-execute');
    if (modal) modal.classList.add('hidden');
}

async function submitPmExecution(event) {
    event.preventDefault();
    const btn = document.getElementById('pm-form-btn-submit');
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Menyimpan...';

    const form = document.getElementById('form-pm-execute');
    const formData = new FormData(form);

    const payload = {
        schedule_id: formData.get('schedule_id'),
        master_id: formData.get('master_id'),
        execution_date: formData.get('execution_date'),
        executor_name: formData.get('executor_name'),
        executor_type: formData.get('executor_type'),
        condition_rating: formData.get('condition_rating'),
        finding_notes: formData.get('finding_notes'),
        action_taken: formData.get('action_taken'),
        photo_before_url: formData.get('photo_before_url'),
        photo_after_url: formData.get('photo_after_url'),
        create_ticket: formData.get('create_ticket') === 'on'
    };

    try {
        const res = await fetch('/api/ops/pm/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await res.json();

        if (result.success) {
            alert('✓ Laporan pemeliharaan berhasil disimpan!' + (result.ticket_id ? ' Tiket sarpras diterbitkan: ' + result.ticket_id : ''));
            closeModalPmExecute();
            form.reset();
            loadPmData();
        } else {
            alert('Gagal menyimpan: ' + (result.error || 'Terjadi kesalahan'));
        }
    } catch (err) {
        alert('Error koneksi: ' + err.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-check"></i> Simpan Laporan Pelaksanaan';
    }
}

function openPmPhotoPreview(url, title) {
    const modal = document.getElementById('modal-pm-photo-view');
    const img = document.getElementById('pm-photo-preview-img');
    const t = document.getElementById('pm-photo-preview-title');
    if (modal && img) {
        img.src = url;
        if (t) t.innerText = title || 'Foto Bukti Pelaksanaan';
        modal.classList.remove('hidden');
    }
}

function closePmPhotoPreview() {
    const modal = document.getElementById('modal-pm-photo-view');
    if (modal) modal.classList.add('hidden');
}

function escapeHtml(text) {
    if (!text) return '';
    return String(text).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
</script>
"""
