/******************************\
 *  INITIALIZE
\******************************/ 

drop database IF EXISTS $database;
create database $database;
use $database;

/******************************\
 * TABLES
\******************************/ 

/***** APP *****/

create table dockerFlaskManager(
    version varchar(20) primary key not null
);

/***** DOCKER *****/

create table dockerContainer(
    id varchar(64) primary key not null,
    name varchar(100) not null,
    image varchar(100) not null
);


/***** DOCKER COMPOSER *****/

create table dockerComposition(
    id varchar(36) primary key not null,
    volumes_path varchar(300) not null,
    name varchar(100) not null,
    version varchar(50) not null
);

create table dockerCompositionContainer(
    composition varchar(36) not null,
    container varchar(64) not null,
    primary key (composition, container),
    foreign key (composition) references dockerComposition(id),
    foreign key (container) references dockerContainer(id)
);

create table dockerComposeOrder(
    id varchar(36) primary key not null,
    composition varchar(36) not null,
    cmd varchar(50) not null,
    args varchar(300),
    status varchar(20),
    foreign key (composition) references dockerComposition(id)
);

/***** USER *****/

create table user(
    id varchar(36) primary key not null,
    username varchar(1000) COLLATE latin1_general_cs not null,
    mdp varchar(1000) COLLATE latin1_general_cs not null,
    token varchar(36) unique,
    expiration_date datetime
);

create table accountPrivilege(
    id varchar(36) primary key not null,
    label varchar(256) not null unique,
    roles varchar(256) not null,
    editable bool not null default 1
);

create table userAccount(
    id varchar(36) primary key not null,
    idU varchar(36) not null,
    idP varchar(36) not null,
    is_authenticated bool not null default 0,
    is_active bool not null default 0,
    is_disabled bool not null default 0,
    language varchar(256) not null default "fr",
    foreign key (idU) references user(id),
    foreign key (idP) references accountPrivilege(id)
);


/***** RESOURCE *****/

create table resourceKey(
    id varchar(36) primary key not null,
    resource varchar(36) not null,
    resource_type varchar(150) not null,
    user varchar(36),
    resource_key varchar(250) not null,
    constraint unique_key unique (resource, user),
    foreign key (user) references user(id)
);

/***** JOBS *****/

create table job(
    name varchar(50) primary key not null,
    state varchar(20) not null default "IDLE",
    last_exit_code int
);