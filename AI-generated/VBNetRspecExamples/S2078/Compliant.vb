Imports Microsoft.AspNetCore.Mvc
Imports System.DirectoryServices
Imports System.Text.RegularExpressions

Public Class S2078DotnetCompliant
    Inherits Controller

    Public Function Authenticate(User As String, Pass As String) As IActionResult
        ' restrict the username and password to letters only
        If Not Regex.IsMatch(User, "^[a-zA-Z]+$") OrElse Not Regex.IsMatch(Pass, "^[a-zA-Z]+$") Then
            Return BadRequest()
        End If

        Dim Directory As New DirectoryEntry("LDAP://ou=system")
        Dim Search As New DirectorySearcher(Directory)

        Search.Filter = "(&(uid=" + User + ")(userPassword=" + Pass + "))"

        Return Json(Search.FindOne() IsNot Nothing)
    End Function
End Class
