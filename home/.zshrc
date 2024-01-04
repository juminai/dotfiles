#!/bin/zsh
SHELL=$(which zsh || echo '/bin/zsh')

fpath=(usr/share/zsh/site-functions $fpath)

setopt autocd              # change directory just by typing its name
setopt interactivecomments # allow comments in interactive mode
setopt magicequalsubst     # enable filename expansion for arguments of the form ‘anything=expression’
setopt nonomatch           # hide error message if there is no match for the pattern
setopt notify              # report the status of background jobs immediately
setopt numericglobsort     # sort filenames numerically when it makes sense
setopt promptsubst         # enable command substitution in prompt
setopt MENU_COMPLETE       # Automatically highlight first element of completion menu
setopt AUTO_LIST           # Automatically list choices on ambiguous completion.
setopt COMPLETE_IN_WORD    # Complete from both ends of a word.

# enable completion features
autoload -Uz compinit
compinit -i

zstyle ':completion:*:*:*:*:*' menu select
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}' # case insensitive tab completion

zstyle ':completion:*' use-cache on
zstyle ':completion:*' cache-path "$HOME/.cache/.zcompcache"

# Define completers
zstyle ':completion:*' completer _extensions _complete _approximate

zstyle ':completion:*:*:*:*:corrections' format '%F{yellow}!- %d (errors: %e) -!%f'
zstyle ':completion:*:*:*:*:descriptions' format '%F{blue}-- %D %d --%f'
zstyle ':completion:*:*:*:*:messages' format ' %F{purple} -- %d --%f'
zstyle ':completion:*:*:*:*:warnings' format ' %F{red}-- no matches found --%f'

zstyle ':completion:*' group-name ''
zstyle ':completion:*:default' list-colors ${(s.:.)LS_COLORS}

# Only display some tags for the command cd
zstyle ':completion:*:*:cd:*' tag-order local-directories directory-stack path-directories

# History configurations
HISTFILE="$HOME/.cache/.zsh_history"
HISTSIZE=10000
SAVEHIST=20000
setopt hist_expire_dups_first # delete duplicates first when HISTFILE size exceeds HISTSIZE
setopt hist_ignore_dups       # ignore duplicated commands history list
setopt hist_ignore_space      # ignore commands that start with space
setopt hist_verify            # show command with history expansion to user before running it
setopt share_history          # share command history data

# source plugins
source /usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
source /usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh

cd() {
  builtin cd "$@" && command lsd -A
}

# init starship
eval "$(starship init zsh)"
# setup starship custom prompt
export STARSHIP_CONFIG=$HOME/.config/starship/starship.toml

# alias
alias ..='cd ..'
alias mkdir='mkdir -pv'
alias ls='lsd'
alias l='lsd -a'
alias cat='bat --color always --theme base16 --plain'
alias grep='grep --color=auto'
alias v='nvim'
alias vim='nvim'
alias mv='mv -v'
alias cp='cp -rv'
alias rm='rm -rfv'
alias gc='git clone'
alias q='exit'
alias fetch='clear ; fetch'
alias footrc='nvim $HOME/.config/foot/foot.ini'

# pacman install
alias paci="yay -Slq | fzf --prompt=' ' --color=bw -m --preview 'cat <(yay -Si {1}) <(yay -Fl {1} | awk \"{print \$2}\")' | xargs -ro yay -S --needed"

# pacman remove
alias pacr="yay -Qq | fzf --prompt=' ' --color=bw -m --preview 'yay -Qi {1}' | xargs -ro yay -Rns"

# pacman view
alias pac="yay -Qq | fzf --prompt=' ' --color=bw -m --preview 'yay -Qi {1}'"

# pacman clear
alias pacc='yay -Qtdq | yay -Rns -'
