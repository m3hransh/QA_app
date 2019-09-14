create table users(
    id integer primary key autoincrement,
    name text not null,
    password text not null,
    expert boolean not null,
    admin boolean not null
);

create table questions(
    id integer primary key not null,
    question_text text not null,
    answer_text text,
    asked_by_id integer,
    expert_id integer
);