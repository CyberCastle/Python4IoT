Copy file in /etc/polkit-1/localauthority/90-mandatory.d

`sudo cp 99-netmgr-authorization.pkla /etc/polkit-1/localauthority/90-mandatory.d/99-netmgr-authorization.pkla`

Add user to group netdev

`sudo usermod -aG netdev <username>`

Restart polkit framework

`sudo systemctl restart polkit`

Verify permissions with

`nmcli general permissions`
