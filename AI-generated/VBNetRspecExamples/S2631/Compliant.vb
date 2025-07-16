Imports Microsoft.AspNetCore.Mvc
Imports System.Text.RegularExpressions

Namespace S2631
    Public Class Compliant
        Inherits Controller

        Public Function Validate(RegexPattern As String, Input As String) As IActionResult
            Dim Match As Boolean = Regex.IsMatch(Input, Regex.Escape(RegexPattern))

            Return Json(Match)
        End Function
    End Class
End Namespace
