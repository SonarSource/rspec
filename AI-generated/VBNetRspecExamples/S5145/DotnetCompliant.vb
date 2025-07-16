Imports Microsoft.AspNetCore.Mvc
Imports log4net

Public Class S5145DotnetCompliant
    Inherits Controller

    Private Shared ReadOnly _logger As log4net.ILog = log4net.LogManager.GetLogger(System.Reflection.MethodBase.GetCurrentMethod().DeclaringType)

    <HttpGet>
    Public Sub Log(Data As String)
        If Data IsNot Nothing Then
            Data = Data.Replace(vbLf, "_"c).Replace(vbCr, "_"c)
            _logger.Info("Log: " & Data)
        End If
    End Sub
End Class
