### Gitlab setup
On target RPi system:

```
cp docs/gitlab/010_gitlab-runner.sudoers /etc/sudoers.d/010_gitlab-runner 
```

OR

```
visudo -f /etc/sudoers.d/010_gitlab-runner
```
and copy the content of the file in `docs/gitlab/010_gitlab-runners.sudoers`