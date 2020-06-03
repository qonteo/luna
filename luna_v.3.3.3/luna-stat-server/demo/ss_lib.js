/**
 * Created by danields on 27.04.17.
 */

class ApiService {
    constructor(host_change_callback, auth_change_callback) {
        this.host = null;
        this.auth_type = null;
        this.auth_callback = auth_change_callback;
        this.host_callback = host_change_callback;
    }

    _callHttp(url, method, params, timeout) {
        if (params != null)
            url += '?' + Object.entries(params).filter(
                ([key, value]) => value !== '' && value
            ).map(
                ([key, value]) => key + '=' + value
            ).join('&');

        return new Promise(
            (resolve, reject) => {
                fetch(
                    url, {
                        method: method
                    }
                ).then(
                    res => {
                        resolve(
                            new Promise(
                                resolve => resolve(res)
                            )
                        );
                    },
                    reason => reject(reason)
                );
                setTimeout(reject, timeout, 'Timeout');
            }
        );
    }

    setHost(host) {
        this.host = host;
    }

    setAuth(type, credentials) {
        this.auth_type = type;
        this.auth_credentials = credentials;
    }

    checkHost(host) {
        return this._callHttp(
            'http://' + host + '/api/version',
            'GET', null, [200, 201], 2000
        ).then(
            (res) => {
                if (res.status != 200)
                    throw {
                        status: res.status,
                        content: res.content
                    };

                this.approveHost(host);
                return res.json();
            }
        ).then(
            (res) => {
                if (this.host_callback != null)
                    this.host_callback(this.host);
                return res;
            }
        ).catch(
            (reason) => {
                throw reason;
            }
        );
    }

    approveHost(host) {
        this.host = host;
    }

    checkAuth(type, credentials) {
        let params = {event_type: 'match'};
        params[type] = credentials;

        return this._callHttp(
            'http://' + this.host + '/api/events', 'GET',
            params, [200, 400], 2000
        ).then(
            (res) => {
                this.approveAuth(type, credentials);
                return res;
            }
        ).then(
            (res) => {
                let a = {};
                a[this.auth_type] = this.auth_credentials;
                if (this.auth_callback != null)
                    this.auth_callback(a);
                return res;
            }
        ).catch(
            status => {
                if (status > 500)
                    throw 'Unexpected status 500 was returned from host.';
                throw 'Wrong credentials';
            }
        );
    }

    approveAuth(type, credentials) {
        this.auth_type = type;
        this.auth_credentials = credentials;
    }

    query(resource, method, parameters, reconnect) {
        if (this.host == null || this.host === '' || this.auth_credentials == null)
            return new Promise(
                (resolve, reject) => {
                    if (this.host == null || this.host === '')
                        reject('Remote host not configured yet');
                    else
                        reject('User credentials not configured yet');
                }
            );

        let url = this.host + '/' + resource;
        let auth = {};
        auth[this.auth_type] = this.auth_credentials;

        let res;
        if (method !== 'ws') {
            res = this._callHttp(
                'http://' + url, method, Object.assign(auth, parameters), [200, 201], 5000
            ).then(
                res => {
                    if (res.status != 200)
                        throw 'Unexpected status code received ' + res.status;
                    return res;
                }
            ).then(
                res => res.json()
            );
        } else {
            res = create_websocket('ws://' + url, Object.assign(auth, parameters));
        }

        if (!reconnect)
            return res;
        else
            return res.catch(
                err => {
                    console.log('ApiService query error: ' + err);
                    let r = reconnect;
                    if (!(r instanceof Number))
                        r = 5;
                    else if (r < 0)
                        throw 'Max reconnect count exceed.';

                    return this.query(
                        resource, method, parameters, r - 1
                    )
                }
            )
    }
}
