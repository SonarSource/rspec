Imports Microsoft.AspNetCore.Mvc
Imports System.Xml
Imports System.Text.RegularExpressions

Namespace S2091
    Public Class Compliant
        Inherits Controller

        <HttpGet>
        Public Function Authenticate(User As String, Pass As String) As IActionResult
            Dim Doc As New XmlDocument()
            If Not Regex.IsMatch(User, "^[a-zA-Z]+$") OrElse Not Regex.IsMatch(Pass, "^[a-zA-Z]+$") Then
                Return BadRequest()
            End If

            Dim Expression As String = "/users/user[@name='" + User + "' and @pass='" + Pass + "']"

            Return Json(Doc.SelectSingleNode(Expression) IsNot Nothing)
        End Function
    End Class
End Namespace
