Imports Microsoft.AspNetCore.Mvc
Imports MongoDB.Driver
Imports MongoDB.Bson
Imports System.Threading.Tasks

Public Class MessageNoncompliant
    Public Property Id As ObjectId
    Public Property Username As String
    Public Property Content As String
End Class

<ApiController>
<Route("Example")>
Public Class S5147MongodbVbnetDriverNoncompliant
    Inherits ControllerBase

    Private ConnectionString As String
    
    <Route("Example")>
    Public Async Function Example() As Task(Of String)
        Dim Client = New MongoClient(ConnectionString)
        Dim Database = Client.GetDatabase("example")
        Dim Collection = Database.GetCollection(Of MessageNoncompliant)("messages")

        Dim FilterDefinition = Request.Query("filterDefinition")
        Dim FilterDefDocument = MongoDB.Bson.Serialization.BsonSerializer.Deserialize(Of BsonDocument)(FilterDefinition)

        Dim Results = Await Collection.FindAsync(FilterDefDocument)
        Return "Complete"
    End Function
End Class
