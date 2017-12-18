# ansible-bergenholm: Ansible modules for Bergenholm

## はじめに

[Bergenholm](https://github.com/yosshy/bergenholm) とは、以下の特長を持
つネットワークインストールサーバです。

* iPXE の利用: iPXE は x86/x86-64 用ネットワークブートローダです。iPXE
  は多数の機能を持っていますが、Bergenholm は、そのうち、 HTTPによるダ
  ウンロード、独自のスクリプト言語、ホスト依存パラメータ等の機能を使用
  しています。
* ローカルリポジトリ不要: Cobbler や MAAS には、それらが管理するインス
  トール用のローカルリポジトリがありますが、Bergenholm にはローカルリポ
  ジトリを必要としません。もちろん、ローカルリポジトリを作成して、
  Bergenholm にそれを利用させる事も出来ます。
* REST APIの提供: Bergenholm は、テンプレート用、ホスト用、グループ用、
  iPXE用の各 RESTful API を持っています。なお、GUI/WebUI は今のところ
  ありません。
* パラメータの継承: Bergenholm はホストとグループで JSON 型のパラメータ
  を扱います。ホストパラメータはグループのパラメータを(多重)継承する事
  ができ、グループも別のグループのパラメータを継承する事ができます。グ
  ループの定義について特別な制限はありません。
* Jinja2 テンプレート: Bergenholm は Jinja2 形式のテンプレートファイル
  とパラメータを扱う事ができます。Kickstart や Preseed ファイル用途で、
  テンプレートファイルはホストやグループのパラメータを使用する事ができ
  ます。[予約パラメータ](https://github.com/yosshy/bergenholm/blob/master/docs/RESERVED_PARAMS.ja.md)
  を除き、パラメータ定義に制約はありません。
* リモートファイルのストリーミング: Bergenholm はリモートサイト上のカー
  ネルや initrd イメージを取得し、インストール先サーバに対してそのファ
  イルを転送 (ストリーミング) する事ができます。
* 電源制御：Bergenholm はインストール先サーバの電源状態を取得・変更する
  機能があります。対応する電源の種別は IPMI、VMware、libvirt です。
* Flask-PyMongo/Flask-Action ベース: バックエンド DB は MongoDB です。
  また、Python で Bergenholm を開発する事ができます。

元々、Ansible のような構成管理システムから操作される前提で開発されたネッ
トワークインストールサーバだったのですが、特に大きなニーズが無かったた
め、これまで専用の Ansible モジュールが今まで存在しませんでした。しかし、
Ansible Advent Calendar 2017 の 12/22 分にエントリしたので、折角だから
Bergenholm のホストとグループを操作する為のモジュールを書きました。

## 使い方

ホストの操作はこんな感じです。

```
- bergenholm_host:
    uuid: "fb0bafd4-b247-49ba-aabc-884386260e7f"
    params:
      groups:
        - centos7
        - centos.amd64
      hostname: "host1"
      ipaddr: "192.168.0.20"
      netif: ens192
    state: present
```

元々 Bergenholm は JSON 化したパラメータ群を Body として REST API に
POST/PUT する事でホストを登録・更新しますが、この Ansible モジュールで
は params: にホストのパラメータ群を YAML の complex 形式で記述します。

uuid: にはホストのシステム UUID を指定します。Linux OS インストール後で
あれば ```sudo dmidecode -s system-uuid``` コマンドでシステム UUID を調
べる事ができます。また、VMware ESXi であれば pysphere モジュール等で、
Libvirt 環境であれば ```virsh dumpxml <ドメインID>``` で調べる事ができ
ますし、物理マシンであれば BIOS 設定画面で調べられる場合があります。

state: には以下のいずれかを指定します。

* present: エントリが存在する
* absent: エントリが存在しない
* installed: OS のインストールが完了している
* uninstalled: OS のインストールが完了していない

グループの操作も似たり寄ったりです。

```
- bergenholm_group:
    name: centos7
    params:
      groups:
        - centos
      version: 7
    state: present
```

ホスト操作だけですが、VMware ESXi 上で VM を作成してインストールを行う
Playbook (create.yml) を作成したので、参考にして下さい。

事前に playbook.yml 中の ESXi 用アカウント／パスワードと、host_vars/
配下の ansibletest* ファイル中のインストール済み環境の SSH アカウント／
パスワード、IPアドレス等を設定して下さい。
設定後、以下のコマンドを実行して下さい。

```
ansible-playbook -i hosts.ini create.yml
```

delete.yml で作成した VM を削除します。
```
ansible-playbook -i hosts.ini delete.yml
```
