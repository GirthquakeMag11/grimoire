import pprint
from grim.importing import import_module_from_path

lorem_ipsum = """
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Pellentesque ac purus quis ex lobortis ornare finibus auctor ipsum. Aenean gravida velit eu nulla laoreet, quis sodales neque gravida. Donec vulputate scelerisque quam in tincidunt. Donec non metus in ipsum eleifend faucibus. Maecenas velit neque, feugiat quis nunc eu, dapibus vestibulum lacus. Duis semper, eros ac ultrices efficitur, nibh nisi pellentesque felis, in posuere nulla libero sed urna. Etiam sed purus eget felis gravida fermentum. Aliquam ornare, sem non suscipit congue, dui tellus semper enim, ac ultrices dui mi vitae ante. Pellentesque sed dignissim leo, vel convallis felis. Nullam massa magna, facilisis a venenatis id, malesuada vel orci. Orci varius natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Suspendisse venenatis sapien ut nisl placerat, et ultrices ante vestibulum. Donec consectetur lacinia quam nec feugiat. Proin quis egestas erat, ut tempus leo. Nullam aliquam dapibus sapien, id ornare nibh venenatis eget. Nullam convallis fermentum orci, non feugiat arcu hendrerit a.

Vestibulum dapibus dictum dictum. Fusce pharetra vestibulum arcu varius maximus. Suspendisse posuere augue tortor, ac aliquet lectus venenatis pretium. Nunc ultrices sit amet enim quis maximus. Nulla dolor odio, condimentum ut ornare a, vehicula sed massa. Ut ornare luctus libero. Phasellus facilisis efficitur quam eget ullamcorper.

Nulla ultrices laoreet dignissim. Cras semper, libero eu posuere eleifend, libero eros congue urna, in hendrerit risus nibh eget nulla. Proin tempor gravida eros. Nulla sagittis ut quam eu viverra. Fusce et malesuada sapien, a varius nulla. Aliquam erat volutpat. Donec tincidunt a dolor quis ultrices. Integer iaculis nibh vitae turpis interdum molestie. Vestibulum sapien odio, dapibus nec dui bibendum, sodales porta massa. Aliquam egestas ante orci, sed porttitor odio pulvinar mollis. Vivamus suscipit id ligula nec egestas. Suspendisse ultrices arcu turpis, gravida auctor mauris mattis eget. Phasellus tincidunt et magna ac venenatis. Vivamus sed purus nulla. Sed semper convallis faucibus.

Morbi at venenatis neque. Sed ac bibendum eros. In lobortis laoreet urna, at imperdiet orci mattis eleifend. Suspendisse potenti. Aliquam ultrices urna et ex ultricies, efficitur mattis erat semper. Donec venenatis eleifend massa in commodo. Donec venenatis interdum nibh, sed porttitor libero porttitor id. Fusce mattis nunc a magna congue imperdiet. Phasellus magna dolor, ornare eu est a, bibendum laoreet diam. Etiam hendrerit, diam in elementum suscipit, felis leo pharetra ipsum, in convallis nisl lorem et ligula. Mauris consequat sollicitudin odio ac mattis.

Morbi ut varius lectus. Vivamus accumsan, sapien lacinia vulputate maximus, dui tortor tincidunt dolor, nec lobortis magna leo nec ex. Maecenas sagittis sodales mauris ac mollis. Aenean sed dolor nec orci accumsan viverra. Praesent vitae mi eu dui gravida suscipit. Donec bibendum elit augue, non feugiat quam maximus non. Curabitur sit amet sapien ac turpis faucibus egestas sed at urna. Nam egestas finibus sapien eget dictum. Quisque ut odio massa. Etiam mi mauris, dapibus a tempor id, viverra non odio. Nam velit libero, lobortis sit amet eleifend a, pretium nec purus.
"""

mp = r"C:\Users\Customer\Desktop\Github\Grimoire\drft\grim\misc.py"
mod = import_module_from_path(mp)
pprint.pprint(mod.markov_chain(lorem_ipsum))
