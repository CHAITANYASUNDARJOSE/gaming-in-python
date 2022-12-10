use Game_server;

create table Player_Profile (
	PlayerID varchar(32),
	firstName varchar(30),
	lastName varchar(30),
	Cash int default 0,
	Gold int default 0,
	primary key (PlayerID)
);

create table Login_Credentials (
	PlayerID varchar(32),
	password varchar(32),
	primary key (PlayerID),
	foreign key (PlayerID) references Player_Profile (PlayerID) on delete cascade on update cascade
);

create table Mini_Game (
	GameID int,
	No_of_rooms int,
	primary key (GameID)
);

create table Players_in_Game (
	PlayerID varchar(32),
	GameID int,
	RoomID int, 
	primary key (PlayerID,GameID,RoomID),
	foreign key (PlayerID) references Player_Profile (PlayerID) on delete cascade on update cascade,
	foreign key (GameID) references Mini_Game (GameID) on delete cascade on update cascade
);

create table Player_History (
	PlayerID varchar(32),
	GameID int,
	RoomID int,
	Cash int, 
	Gold int,
	primary key (PlayerID,GameID,RoomID),
	foreign key (PlayerID) references Player_Profile (PlayerID) on delete cascade on update cascade,
	foreign key (GameID) references Mini_Game (GameID) on delete cascade on update cascade
);

create table Perks_Available (
	PerkID int(1),
	Name text,
	Description text,
	Price int(4), 
	primary key (PerkID)
);

create table Owned_Perk (
	PlayerID varchar(32),
	PerkID int(1),
	Quantity int, 
	primary key (PlayerID,PerkID),
	foreign key (PlayerID) references Player_Profile (PlayerID) on delete cascade on update cascade,
	foreign key (PerkID) references Perks_Available (PerkID) on delete cascade on update cascade
);

insert into Mini_Game values(1,0);
insert into Mini_Game values(2,0);


insert into Perks_Available values(1,'2x Multiplier','Used to multiply both cash and gold obtained from a game!',4);
insert into Perks_Available values(2,'Head start!','Used to obtain a random headstart between 1 to 10 in Snakes \'n Ladders!',6);