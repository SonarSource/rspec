Imports Microsoft.AspNetCore.Mvc
Imports System.Diagnostics

Namespace S2076
    Public Class Compliant
        Inherits Controller

        Public Sub Run(Binary As String)
            If Binary.Equals("/usr/bin/ls") OrElse Binary.Equals("/usr/bin/cat") Then
                ' only ls and cat commands are authorized
                Dim P As New Process()
                P.StartInfo.FileName = Binary
                P.Start()
            End If
        End Sub
    End Class
End Namespace
