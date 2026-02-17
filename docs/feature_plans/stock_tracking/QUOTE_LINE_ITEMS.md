# Ramjet Plastics — Stock Tracking System
## Quote Line Items

**Prepared by:** Brett Chilton
**Date:** February 11, 2026
**Client:** Ramjet Plastics (Grant)

---

### Project Summary

Real-time stock tracking system using QR-coded cartons and Bluetooth barcode scanners. Eliminates manual stock counting by maintaining a live inventory ledger updated via scan events. Covers finished goods, raw materials, quarterly stocktakes, and management reporting.

---

### Deliverables

| # | Item | Description |
|---|------|-------------|
| 1 | **Database & Product Management** | Stock tracking database schema. Full product management interface (add, edit, delete, search products). Stock threshold configuration per product. |
| 2 | **QR Code Label System** | Unique QR code generation per carton. Printable label PDFs (pink for full cartons, yellow for partial). Batch label generation interface on tablet. |
| 3 | **Stock-In Scanning** | Tablet-based scanning interface for receiving finished goods into stock after production runs. Bluetooth scanner integration (Zebra DS22). Real-time stock level updates. Visual and audio scan feedback. |
| 4 | **Stock-Out Scanning & Order Fulfilment** | Scan cartons out when fulfilling customer orders. Links to existing order management system. Partial box handling (split carton, re-label remainder, enter quantity). |
| 5 | **Stock Dashboard & Search** | Real-time stock level dashboard with colour-coded indicators (green/amber/red). Search and filter by product, colour, status. Drill-down to individual carton history. Spreadsheet export. |
| 6 | **Quarterly Stocktake System** | Stocktake session management. Walk-and-scan verification mode. Live progress tracking (scanned vs expected). Discrepancy detection and reporting. Stock reconciliation. |
| 7 | **Raw Materials Inventory** | Raw material master data management (CRUD). Receive deliveries, record usage, manual adjustments. Stock levels with colour-coded thresholds. Movement history. |
| 8 | **Reports & Data Export** | Stock valuation report. Movement history report (filterable). Point-in-time stock on hand report. Stocktake summary reports. All reports exportable as Excel spreadsheets. |

---

### Infrastructure & Setup

| Item | Description |
|------|-------------|
| **Server Setup** | Application configured to run on Mac Mini M4 (localhost). Accessible to tablets over local WiFi network. |
| **Scanner Integration** | Zebra DS22 Bluetooth barcode scanner integration via HID keyboard mode. No native app or special drivers required. |
| **Tablet Access** | Web application optimised for tablet use (large touch targets, responsive layout). Tablets access system via Mac Mini's local IP address over WiFi. |

---

### Exclusions (Future Phases)

The following items are **not** included in this quote but are noted for future development:

- Automatic raw material deduction against work orders
- Raw material assignment to production runs
- Cross-checking raw material levels against planned work orders
- Automated purchase order generation for low-stock raw materials
- Integration with external accounting/ERP systems
- Barcode scanning via mobile phone camera (current scope uses dedicated Bluetooth scanner only)

---

### Technical Notes

- Integrates with the existing Ramjet order management platform (same application, shared database)
- No additional server hardware required beyond the Mac Mini M4
- No additional software licenses required
- Uses existing WiFi infrastructure
- Standard A4 sticker sheets for label printing (regular printer)
