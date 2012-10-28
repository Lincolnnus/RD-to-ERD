This relational database-ER diagram translation case tool  is a web-based project which consists of the front end module and the back end module.

The ER diagram graphics rendering module is a front end module written in HTML5 and Javascript.
The Relational Diagram translator module is a back end modeul written in Python.
The uploader module consists of the front end HTML form and the back end PHP handler.
	 
1.Front End Modules.

	1.1. The relational database uploader form which is written in html.
	User will need to pass the relational database file(The format of the relational database is introduced in the documentation) for the 	translator to work.

	1.2. The graphic rendering module which is written in html5 and javascript
	This rendering module will display the translated json entity objects and relation objects into an ER diagram.
	The directory needs to be exactly as the renderPath and the renderURL specified in the translate.py file in the translator module.
	
	Web server admin needs to put these files(the "upload" folder and the "render" folder) on the server(apache, etc) for users to access on the web.

2.Back End Modules.

	2.1. The relational database uploader handler which is written in php.
	This handler will move the relational database file to the desired backend for data parsing.

	2.2. The translator module which is written in Python
 	The main function is the translate.py, which will translate the relational database named database.txt to json string of the entity objects in entity_json.txt and the relation objects in relation_json.txt. To run this translator, a CGI(Common Gateway Interface) needs to be installed in the server. 
	
	The translator(the "translator" folder) will need to be located under the CGI-Bin file of the server. 
	
	
	CS4221 Team Li Shaohuan, Hou Li, Zhang Jiao and Dinh Hoang Phuong Thao. All rights reserved. 
