CREATE DATABASE emporium;

{% for user, password in users.items() %}
CREATE USER {{ user }} WITH ENCRYPTED PASSWORD 'md5{{ password }}';
GRANT ALL PRIVILEGES ON DATABASE emporium TO {{ user }};
GRANT emporium TO {{ user }};
{% endfor %}

