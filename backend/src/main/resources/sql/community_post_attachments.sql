create table if not exists post_attachments (
    id bigint auto_increment primary key,
    post_id bigint not null,
    file_key varchar(500) not null,
    original_file_name varchar(255) not null,
    content_type varchar(100) not null,
    file_size bigint not null,
    display_order int not null,
    created_at datetime(6) not null,
    updated_at datetime(6) not null,
    constraint fk_post_attachments_post foreign key (post_id) references posts (id)
);

create index idx_post_attachments_post_id_order on post_attachments (post_id, display_order, id);
