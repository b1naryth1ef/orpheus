CREATE USER emporium WITH PASSWORD '{{ password }}';
CREATE DATABASE emporium;
GRANT ALL PRIVILEGES ON DATABASE emporium TO emporium;

{% for user, password in users.items() %}
CREATE USER {{ user }} WITH PASSWORD 'md5{{ password }}';
GRANT ALL PRIVILEGES ON DATABASE emporium TO {{ user }};
{% endfor %}

