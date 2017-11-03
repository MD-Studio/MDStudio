cbdir=$(dirname $(readlink -f ${BASH_SOURCE[0]}))
_kill-wrap () { compose-modular exec $1 pkill python; }

alias compose-modular='docker-compose -f docker-compose-modular.yml'
alias kill-component='_kill-wrap'
alias kill-crossbar='compose-modular exec crossbar pkill crossbar'
alias lie-cli='winpty docker-compose -f docker-compose-modular.yml run --rm cli'
alias local-crossbar="MD_GLOBAL_LOG=1 python -u -m crossbar start --cbdir $cbdir --config $cbdir/data/crossbar/config_modular.json --logdir $cbdir/data/logs --loglevel info"