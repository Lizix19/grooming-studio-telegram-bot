create table vid (
    id_vid int primary key,
    nazvanie varchar(255) not null
);

create table poroda_pitomtsev (
    id_porody int primary key,
    id_vid int not null,
    nazvanie varchar(255) not null,
    sredniy_ves decimal(5, 2),
    dlina_shersti varchar(255)
);

create table klienty (
    id_klienta int primary key,
    imya varchar(255) not null,
    familiya varchar(255) not null,
    telefon varchar(20),
    email varchar(255),
    adres varchar(255)
);

create table pitomtsy (
    id_pitomtsa int primary key,
    id_klienta int not null,
    id_poroda int not null,
    imya varchar(255) not null,
    data_rozhdeniya date not null
);

create table status (
    id_status int primary key,
    nazvanie varchar(255) not null
);

create table sotrudniki (
    id_sotrudnika int primary key,
    familiya varchar(255) not null,
    imya varchar(255) not null,
    dolzhnost varchar(255) not null,
    stazh_raboty int,
    informatsiya_ob_obuchenii text
);

create table uslugi (
    id_uslugi int primary key,
    nazvanie varchar(255) not null,
    opisanie text,
    stoimost decimal(10, 2) not null,
    vremya_vypolneniya int
);

create table zapis_na_uslugu (
    id_zapisi int primary key,
    id_sotrudnika int not null,
    id_pitomtsa int not null,
    data_i_vremya_zapisi datetime not null,
    id_status int not null
);

create table dop_materialy (
    id_dop_material int primary key,
    naimenovanie varchar(255) not null,
    tsena decimal(10, 2) not null
);

create table uslugi_v_zapisi (
    id_uslugi int not null,
    id_zapisi int not null,
    primary key (id_uslugi, id_zapisi)
);

create table dop_v_zapisi (
    id_zapis int not null,
    id_dop_material int not null,
    primary key (id_zapis, id_dop_material)
);

create table otzyvy (
    id_otzyva int primary key,
    id_zapis int not null,
    otsenka int,
    kommentariy text
);




alter table poroda_pitomtsev
add constraint fk_poroda_pitomtsev_vid
foreign key (id_vid) references vid(id_vid);

alter table pitomtsy
add constraint fk_pitomtsy_klienty
foreign key (id_klienta) references klienty(id_klienta);

alter table pitomtsy
add constraint fk_pitomtsy_poroda_pitomtsev
foreign key (id_poroda) references poroda_pitomtsev(id_porody);

alter table zapis_na_uslugu
add constraint fk_zapis_na_uslugu_sotrudniki
foreign key (id_sotrudnika) references sotrudniki(id_sotrudnika);

alter table zapis_na_uslugu
add constraint fk_zapis_na_uslugu_pitomtsy
foreign key (id_pitomtsa) references pitomtsy(id_pitomtsa);

alter table zapis_na_uslugu
add constraint fk_zapis_na_uslugu_status
foreign key (id_status) references status(id_status);

alter table uslugi_v_zapisi
add constraint fk_uslugi_v_zapisi_uslugi
foreign key (id_uslugi) references uslugi(id_uslugi);

alter table uslugi_v_zapisi
add constraint fk_uslugi_v_zapisi_zapis_na_uslugu
foreign key (id_zapisi) references zapis_na_uslugu(id_zapisi);

alter table dop_v_zapisi
add constraint fk_dop_v_zapisi_zapis_na_uslugu
foreign key (id_zapis) references zapis_na_uslugu(id_zapisi);

alter table dop_v_zapisi
add constraint fk_dop_v_zapisi_dop_materialy
foreign key (id_dop_material) references dop_materialy(id_dop_material);

alter table otzyvy
add constraint fk_otzyvy_zapis_na_uslugu
foreign key (id_zapis) references zapis_na_uslugu(id_zapisi);


ALTER TABLE zapis_na_uslugu
ADD k_oplate DECIMAL(10, 2) NOT NULL DEFAULT 0;

UPDATE zapis_na_uslugu
SET k_oplate = (
    COALESCE((
        SELECT SUM(u.stoimost)
        FROM uslugi_v_zapisi uvz
        JOIN uslugi u ON uvz.id_uslugi = u.id_uslugi
        WHERE uvz.id_zapisi = zapis_na_uslugu.id_zapisi
    ), 0)
    +
    COALESCE((
        SELECT SUM(dm.tsena)
        FROM dop_v_zapisi dvz
        JOIN dop_materialy dm ON dvz.id_dop_material = dm.id_dop_material
        WHERE dvz.id_zapis = zapis_na_uslugu.id_zapisi
    ), 0)
);
