Imports Microsoft.AspNetCore.Mvc
Imports log4net

Public Class S5145DotnetNoncompliant
    Inherits Controller

    Private Shared ReadOnly _logger As log4net.ILog = log4net.LogManager.GetLogger(System.Reflection.MethodBase.GetCurrentMethod().DeclaringType)

    <HttpGet>
    Public Sub Log(Data As String)
        If Data IsNot Nothing Then
            _logger.Info("Log: " & Data) ' Noncompliant
        End If
    End Sub
End Class
