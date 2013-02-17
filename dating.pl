  use strict;
  use warnings;
  use Irssi;

  our $VERSION = '1.00';
  our %IRSSI = (
      authors     => 'Christian Dietrich',
      contact     => 'stettberger@dokucode.de',
      name        => 'Have fun with friends protocol',
      description => 'Implements the BWFP',
      license     => 'Public Domain',
    );

Irssi::signal_add 'message private', 'dating_message';
Irssi::settings_add_str("dating", "dating_pythonscript", "~/.irssi/dating/dating.py");
Irssi::settings_add_str("dating", "dating_statefile", "~/.irssi/dating/state");
Irssi::settings_add_str("dating", "dating_bang_list", "nick1 nick2");

sub dating_message {
     my ($server, $msg, $nick, $nick_addr, $target) = @_;
     if ($msg =~ m/^BWFP:/) { # only operate in these channels
         my $own_nickname = $server->{nick};
         my $script = Irssi::settings_get_str('dating_pythonscript');
         my $statefile = Irssi::settings_get_str('dating_statefile');
         my $bang_list = Irssi::settings_get_str('dating_bang_list');
         my $cmd = "echo msg $nick $msg | python $script $statefile $own_nickname $bang_list";
         my $response = `$cmd`;

         for $cmd (split(/\n/,$response)) {
             $server->command($cmd);
         }
     }
}

Irssi::command_bind 'dating_start', \&cmd_dating_start;

sub cmd_dating_start {
    my ($args, $server, $win_item) = @_;

    my $own_nickname = $server->{nick};
    my $script = Irssi::settings_get_str('dating_pythonscript');
    my $statefile = Irssi::settings_get_str('dating_statefile');
    my $bang_list = Irssi::settings_get_str('dating_bang_list');
    my $cmd = "echo start $args | python $script $statefile $own_nickname $bang_list";
    my $response = `$cmd`;
    for $cmd (split(/\n/,$response)) {
        $server->command($cmd);
    }
}
