# Excel Companion (Optional)

You can export data from the Streamlit app and then build:

- Power Query refresh
- Pivot tables + slicers
- Conditional formatting
- Power Pivot (Data Model)
- VBA security (chart visible only 9 AM–5 PM)

## VBA Security Requirement (#4)

Import `security_vba.bas` into Excel:

1. Excel → Developer → Visual Basic
2. File → Import File… → select `security_vba.bas`
3. Create a sheet named **Dashboard**
4. Insert a chart on Dashboard (top 10 by Volume 24h)
5. Put message cell at `B2` (or change code)

Add this into `ThisWorkbook`:

```vb
Private Sub Workbook_Open()
    SecurityModule.RefreshVisibility
    SecurityModule.StartAutoRefresh
End Sub

Private Sub Workbook_BeforeClose(Cancel As Boolean)
    SecurityModule.StopAutoRefresh
End Sub
```
