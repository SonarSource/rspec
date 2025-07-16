Imports Microsoft.AspNetCore.Mvc
Imports System.Diagnostics

Namespace S2076
    Public Class Noncompliant
        Inherits Controller

        Public Sub Run(Binary As String)
            Dim P As New Process()
            P.StartInfo.FileName = Binary
            P.Start()
        End Sub
    End Class
End Namespace
