Attribute VB_Name = "SecurityModule"
Option Explicit

Public NextRun As Date

Sub RefreshVisibility()
    Dim ws As Worksheet
    Set ws = ThisWorkbook.Sheets("Dashboard")

    Dim hr As Integer
    hr = Hour(Now)

    Dim chartObj As ChartObject
    Set chartObj = ws.ChartObjects(1)

    Dim msgCell As Range
    Set msgCell = ws.Range("B2")

    If hr >= 9 And hr < 17 Then
        chartObj.Visible = True
        msgCell.Value = ""
    Else
        chartObj.Visible = False
        msgCell.Value = "Please open in working hours ( 9 am to 5 pm )"
    End If
End Sub

Sub StartAutoRefresh()
    Call StopAutoRefresh
    NextRun = Now + TimeValue("00:01:00")
    Application.OnTime NextRun, "Tick"
End Sub

Sub StopAutoRefresh()
    On Error Resume Next
    Application.OnTime EarliestTime:=NextRun, Procedure:="Tick", Schedule:=False
    On Error GoTo 0
End Sub

Sub Tick()
    RefreshVisibility
    StartAutoRefresh
End Sub
