Imports System.Xml
Imports System.Security
Imports Microsoft.AspNetCore.Mvc

Public Class S6399DotnetCompliant
    Inherits Controller

    Public Async Sub Example(Username As String)
        Dim Writer As XmlWriter = XmlWriter.Create("data.xml")
        Await Writer.WriteRawAsync(
            $"<user>
                <username>{SecurityElement.Escape(Username)}</username>
                <role>user</role>
            </user>"
        )
        Await Writer.DisposeAsync()
    End Sub
End Class

Public Class S6399DotnetCompliant2
    Inherits Controller

    Public Async Sub Example(Username As String)
        Dim Doc As New XmlDocument()
        Dim User As XmlElement = Doc.CreateElement("user")
        Doc.AppendChild(User)

        Dim UsernameElement As XmlElement = Doc.CreateElement("username")
        User.AppendChild(UsernameElement)
        UsernameElement.InnerText = Username

        Dim Role As XmlElement = Doc.CreateElement("role")
        User.AppendChild(Role)
        Role.InnerText = "user"
        Doc.Save("data.xml")
    End Sub
End Class
